from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import numpy as np
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Directories
UPLOADS_DIR = ROOT_DIR / "uploads"
DATASET_DIR = UPLOADS_DIR / "dataset"
QUERIES_DIR = UPLOADS_DIR / "queries"
DATA_DIR = ROOT_DIR / "data"

for d in [DATASET_DIR, QUERIES_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for ML models
feature_extractor = None
faiss_index = None
image_paths = []
features_array = None
executor = ThreadPoolExecutor(max_workers=2)

# Models
class ImageInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    filepath: str
    category: str = "unknown"
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SearchResult(BaseModel):
    image_id: str
    filename: str
    filepath: str
    category: str
    similarity_score: float

class SearchResponse(BaseModel):
    query_image: str
    results: List[SearchResult]
    search_time_ms: float
    total_indexed: int

class LogEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: str
    message: str
    category: str = "general"

class DatasetStats(BaseModel):
    total_images: int
    categories: dict
    index_built: bool
    index_size: int

async def log_activity(message: str, level: str = "INFO", category: str = "general"):
    """Log activity to database"""
    log_entry = LogEntry(message=message, level=level, category=category)
    doc = log_entry.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.logs.insert_one(doc)
    logger.info(f"[{category}] {message}")

def load_feature_extractor():
    """Load ResNet50 model for feature extraction"""
    global feature_extractor
    if feature_extractor is None:
        try:
            from tensorflow.keras.applications import ResNet50
            from tensorflow.keras.models import Model
            base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
            feature_extractor = base_model
            logger.info("ResNet50 feature extractor loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load feature extractor: {e}")
            raise
    return feature_extractor

def extract_features(image_path: str) -> np.ndarray:
    """Extract features from a single image"""
    from tensorflow.keras.applications.resnet50 import preprocess_input
    from tensorflow.keras.preprocessing import image as keras_image
    
    model = load_feature_extractor()
    img = keras_image.load_img(image_path, target_size=(224, 224))
    img_array = keras_image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)
    features = model.predict(img_array, verbose=0)
    return features.flatten()

def build_faiss_index_sync(features: np.ndarray):
    """Build FAISS index synchronously"""
    import faiss
    dimension = features.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity after normalization)
    # Normalize features for cosine similarity
    faiss.normalize_L2(features)
    index.add(features)
    return index

async def build_index():
    """Build FAISS index from all dataset images"""
    global faiss_index, image_paths, features_array
    
    await log_activity("Starting index building process...", category="indexing")
    
    # Get all images from dataset directory
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    all_images = []
    
    for root, dirs, files in os.walk(DATASET_DIR):
        for file in files:
            if Path(file).suffix.lower() in image_extensions:
                all_images.append(Path(root) / file)
    
    if not all_images:
        await log_activity("No images found in dataset", level="WARNING", category="indexing")
        return False
    
    await log_activity(f"Found {len(all_images)} images to index", category="indexing")
    
    # Extract features
    features_list = []
    image_paths = []
    
    for i, img_path in enumerate(all_images):
        try:
            features = await asyncio.get_event_loop().run_in_executor(
                executor, extract_features, str(img_path)
            )
            features_list.append(features)
            image_paths.append(str(img_path))
            
            if (i + 1) % 10 == 0:
                await log_activity(f"Processed {i + 1}/{len(all_images)} images", category="indexing")
        except Exception as e:
            await log_activity(f"Failed to process {img_path}: {e}", level="ERROR", category="indexing")
    
    if not features_list:
        await log_activity("No features extracted", level="ERROR", category="indexing")
        return False
    
    features_array = np.array(features_list).astype('float32')
    
    # Build FAISS index
    faiss_index = await asyncio.get_event_loop().run_in_executor(
        executor, build_faiss_index_sync, features_array.copy()
    )
    
    # Save index and paths
    import faiss
    faiss.write_index(faiss_index, str(DATA_DIR / "faiss_index.bin"))
    np.save(str(DATA_DIR / "features.npy"), features_array)
    with open(DATA_DIR / "image_paths.json", "w") as f:
        json.dump(image_paths, f)
    
    await log_activity(f"Index built successfully with {len(image_paths)} images", category="indexing")
    return True

async def load_index():
    """Load existing FAISS index"""
    global faiss_index, image_paths, features_array
    
    index_path = DATA_DIR / "faiss_index.bin"
    features_path = DATA_DIR / "features.npy"
    paths_file = DATA_DIR / "image_paths.json"
    
    if index_path.exists() and features_path.exists() and paths_file.exists():
        import faiss
        faiss_index = faiss.read_index(str(index_path))
        features_array = np.load(str(features_path))
        with open(paths_file, "r") as f:
            image_paths = json.load(f)
        logger.info(f"Loaded existing index with {len(image_paths)} images")
        return True
    return False

# Routes
@api_router.get("/")
async def root():
    return {"message": "Animal Image Similarity Search API"}

@api_router.post("/upload-dataset")
async def upload_dataset_images(
    files: List[UploadFile] = File(...),
    category: str = Form(default="unknown")
):
    """Upload images to the dataset"""
    uploaded = []
    category_dir = DATASET_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        if not file.content_type.startswith('image/'):
            continue
        
        file_id = str(uuid.uuid4())
        ext = Path(file.filename).suffix or '.jpg'
        new_filename = f"{file_id}{ext}"
        filepath = category_dir / new_filename
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Save to database
        image_info = ImageInfo(
            id=file_id,
            filename=file.filename,
            filepath=str(filepath),
            category=category
        )
        doc = image_info.model_dump()
        doc['uploaded_at'] = doc['uploaded_at'].isoformat()
        await db.images.insert_one(doc)
        uploaded.append(image_info.model_dump())
    
    await log_activity(f"Uploaded {len(uploaded)} images to category '{category}'", category="upload")
    return {"uploaded": len(uploaded), "images": uploaded}

@api_router.post("/search")
async def search_similar_images(
    file: UploadFile = File(...),
    top_k: int = Form(default=10),
    threshold: float = Form(default=0.0)
):
    """Search for similar images"""
    global faiss_index, image_paths, features_array
    
    if faiss_index is None:
        loaded = await load_index()
        if not loaded:
            raise HTTPException(status_code=400, detail="Index not built. Please build the index first.")
    
    # Save query image
    query_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix or '.jpg'
    query_path = QUERIES_DIR / f"{query_id}{ext}"
    
    with open(query_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    await log_activity(f"Processing search query: {file.filename}", category="search")
    
    import time
    start_time = time.time()
    
    # Extract features from query image
    try:
        query_features = await asyncio.get_event_loop().run_in_executor(
            executor, extract_features, str(query_path)
        )
    except Exception as e:
        await log_activity(f"Failed to extract features: {e}", level="ERROR", category="search")
        raise HTTPException(status_code=400, detail=f"Failed to process image: {e}")
    
    # Normalize query features
    import faiss
    query_features = query_features.reshape(1, -1).astype('float32')
    faiss.normalize_L2(query_features)
    
    # Search
    k = min(top_k, len(image_paths))
    distances, indices = faiss_index.search(query_features, k)
    
    search_time = (time.time() - start_time) * 1000
    
    # Build results
    results = []
    for i, (idx, score) in enumerate(zip(indices[0], distances[0])):
        if idx < 0 or score < threshold:
            continue
        
        img_path = image_paths[idx]
        category = Path(img_path).parent.name
        
        results.append(SearchResult(
            image_id=str(idx),
            filename=Path(img_path).name,
            filepath=img_path,
            category=category,
            similarity_score=float(score)
        ))
    
    await log_activity(
        f"Search completed: found {len(results)} results in {search_time:.2f}ms",
        category="search"
    )
    
    return SearchResponse(
        query_image=str(query_path),
        results=results,
        search_time_ms=search_time,
        total_indexed=len(image_paths)
    )

@api_router.post("/build-index")
async def trigger_build_index():
    """Trigger index building"""
    success = await build_index()
    if success:
        return {"status": "success", "message": "Index built successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to build index")

@api_router.get("/dataset-stats")
async def get_dataset_stats():
    """Get dataset statistics"""
    # Count images by category
    categories = {}
    total = 0
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    if DATASET_DIR.exists():
        for cat_dir in DATASET_DIR.iterdir():
            if cat_dir.is_dir():
                count = sum(1 for f in cat_dir.iterdir() 
                           if f.is_file() and f.suffix.lower() in image_extensions)
                if count > 0:
                    categories[cat_dir.name] = count
                    total += count
    
    index_exists = (DATA_DIR / "faiss_index.bin").exists()
    index_size = len(image_paths) if image_paths else 0
    
    return DatasetStats(
        total_images=total,
        categories=categories,
        index_built=index_exists,
        index_size=index_size
    )

@api_router.get("/logs")
async def get_logs(limit: int = 100, category: Optional[str] = None):
    """Get activity logs"""
    query = {}
    if category:
        query["category"] = category
    
    logs = await db.logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    return logs

@api_router.delete("/clear-logs")
async def clear_logs():
    """Clear all logs"""
    await db.logs.delete_many({})
    return {"status": "success", "message": "Logs cleared"}

@api_router.get("/categories")
async def get_categories():
    """Get all categories in the dataset"""
    categories = []
    if DATASET_DIR.exists():
        for cat_dir in DATASET_DIR.iterdir():
            if cat_dir.is_dir():
                categories.append(cat_dir.name)
    return {"categories": sorted(categories)}

@api_router.delete("/clear-dataset")
async def clear_dataset():
    """Clear all dataset images and index"""
    global faiss_index, image_paths, features_array
    
    # Clear dataset directory
    if DATASET_DIR.exists():
        shutil.rmtree(DATASET_DIR)
        DATASET_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clear index files
    for f in ["faiss_index.bin", "features.npy", "image_paths.json"]:
        path = DATA_DIR / f
        if path.exists():
            path.unlink()
    
    # Clear database
    await db.images.delete_many({})
    
    # Reset globals
    faiss_index = None
    image_paths = []
    features_array = None
    
    await log_activity("Dataset cleared", category="system")
    return {"status": "success", "message": "Dataset cleared"}

@api_router.get("/sample-categories")
async def get_sample_categories():
    """Return sample animal categories for demo - organized by type"""
    categories = {
        "mammals": ["cat", "dog", "lion", "tiger", "elephant", "bear", "wolf", "fox", "deer", "zebra", "giraffe", "rabbit", "panda", "koala", "horse", "cow"],
        "birds": ["eagle", "owl", "parrot", "penguin", "flamingo", "peacock"],
        "fish_and_sea": ["shark", "dolphin", "whale", "turtle", "octopus", "goldfish", "clownfish"],
        "reptiles_and_amphibians": ["snake", "lizard", "crocodile", "frog"],
        "insects": ["butterfly", "bee"]
    }
    return {"categories": categories}

@api_router.get("/images/{image_type}/{category}/{filename}")
async def serve_image(image_type: str, category: str, filename: str):
    """Serve images through API endpoint for Kubernetes compatibility"""
    from fastapi.responses import FileResponse
    
    if image_type == "dataset":
        file_path = DATASET_DIR / category / filename
    elif image_type == "queries":
        file_path = QUERIES_DIR / filename
    else:
        raise HTTPException(status_code=404, detail="Invalid image type")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Determine content type
    suffix = file_path.suffix.lower()
    content_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp'
    }
    content_type = content_types.get(suffix, 'application/octet-stream')
    
    return FileResponse(file_path, media_type=content_type)

# Include the router in the main app
app.include_router(api_router)

# Serve static files for uploaded images
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Load index on startup if available"""
    await load_index()
    await log_activity("Application started", category="system")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
