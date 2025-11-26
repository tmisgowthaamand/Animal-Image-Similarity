import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { Search, Upload, Database, BarChart3, FileText, Settings, Trash2, RefreshCw, Image, Loader2, X, ChevronDown, ChevronUp, Zap, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  // State
  const [activeTab, setActiveTab] = useState("search");
  const [queryImage, setQueryImage] = useState(null);
  const [queryPreview, setQueryPreview] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searchStats, setSearchStats] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [topK, setTopK] = useState(10);
  const [threshold, setThreshold] = useState(0);
  const [datasetStats, setDatasetStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [isBuilding, setIsBuilding] = useState(false);
  const [uploadFiles, setUploadFiles] = useState([]);
  const [uploadCategory, setUploadCategory] = useState("unknown");
  const [isUploading, setIsUploading] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [sampleCategories, setSampleCategories] = useState([]);
  const [logsExpanded, setLogsExpanded] = useState(true);

  // Fetch initial data
  const fetchDatasetStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/dataset-stats`);
      setDatasetStats(response.data);
    } catch (error) {
      console.error("Failed to fetch dataset stats:", error);
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/logs?limit=50`);
      setLogs(response.data);
    } catch (error) {
      console.error("Failed to fetch logs:", error);
    }
  }, []);

  const fetchSampleCategories = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/sample-categories`);
      setSampleCategories(response.data.categories);
    } catch (error) {
      console.error("Failed to fetch categories:", error);
    }
  }, []);

  useEffect(() => {
    fetchDatasetStats();
    fetchLogs();
    fetchSampleCategories();
  }, [fetchDatasetStats, fetchLogs, fetchSampleCategories]);

  // Handlers
  const handleQueryImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setQueryImage(file);
      setQueryPreview(URL.createObjectURL(file));
      setSearchResults([]);
      setSearchStats(null);
    }
  };

  const handleSearch = async () => {
    if (!queryImage) {
      toast.error("Please select a query image");
      return;
    }

    if (!datasetStats?.index_built) {
      toast.error("Index not built. Please build the index first.");
      return;
    }

    setIsSearching(true);
    const formData = new FormData();
    formData.append("file", queryImage);
    formData.append("top_k", topK);
    formData.append("threshold", threshold);

    try {
      const response = await axios.post(`${API}/search`, formData);
      setSearchResults(response.data.results);
      setSearchStats({
        searchTime: response.data.search_time_ms,
        totalIndexed: response.data.total_indexed,
        resultsCount: response.data.results.length
      });
      toast.success(`Found ${response.data.results.length} similar images`);
      fetchLogs();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Search failed");
    } finally {
      setIsSearching(false);
    }
  };

  const handleBuildIndex = async () => {
    setIsBuilding(true);
    try {
      await axios.post(`${API}/build-index`);
      toast.success("Index built successfully!");
      fetchDatasetStats();
      fetchLogs();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to build index");
    } finally {
      setIsBuilding(false);
    }
  };

  const handleUploadDataset = async () => {
    if (uploadFiles.length === 0) {
      toast.error("Please select files to upload");
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    uploadFiles.forEach(file => formData.append("files", file));
    formData.append("category", uploadCategory);

    try {
      const response = await axios.post(`${API}/upload-dataset`, formData);
      toast.success(`Uploaded ${response.data.uploaded} images`);
      setUploadFiles([]);
      fetchDatasetStats();
      fetchLogs();
    } catch (error) {
      toast.error("Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  const handleClearDataset = async () => {
    if (!window.confirm("Are you sure you want to clear all dataset images?")) return;
    try {
      await axios.delete(`${API}/clear-dataset`);
      toast.success("Dataset cleared");
      fetchDatasetStats();
      fetchLogs();
      setSearchResults([]);
    } catch (error) {
      toast.error("Failed to clear dataset");
    }
  };

  const handleClearLogs = async () => {
    try {
      await axios.delete(`${API}/clear-logs`);
      setLogs([]);
      toast.success("Logs cleared");
    } catch (error) {
      toast.error("Failed to clear logs");
    }
  };

  const getImageUrl = (filepath) => {
    // Parse filepath like /app/backend/uploads/dataset/dog/dog1.jpg
    // or /app/backend/uploads/queries/abc.jpg
    const parts = filepath.split('/uploads/');
    if (parts.length < 2) return filepath;
    
    const relativePath = parts[1]; // dataset/dog/dog1.jpg or queries/abc.jpg
    const pathParts = relativePath.split('/');
    
    if (pathParts[0] === 'dataset' && pathParts.length >= 3) {
      // dataset/category/filename -> /api/images/dataset/category/filename
      return `${API}/images/dataset/${pathParts[1]}/${pathParts.slice(2).join('/')}`;
    } else if (pathParts[0] === 'queries' && pathParts.length >= 2) {
      // queries/filename -> /api/images/queries/_/filename
      return `${API}/images/queries/_/${pathParts.slice(1).join('/')}`;
    }
    
    return `${BACKEND_URL}/uploads/${relativePath}`;
  };

  // Analytics calculations
  const getAnalytics = () => {
    if (searchResults.length === 0) return null;
    
    const avgSimilarity = searchResults.reduce((sum, r) => sum + r.similarity_score, 0) / searchResults.length;
    const categoryDist = searchResults.reduce((acc, r) => {
      acc[r.category] = (acc[r.category] || 0) + 1;
      return acc;
    }, {});
    const maxSimilarity = Math.max(...searchResults.map(r => r.similarity_score));
    const minSimilarity = Math.min(...searchResults.map(r => r.similarity_score));

    return { avgSimilarity, categoryDist, maxSimilarity, minSimilarity };
  };

  const analytics = getAnalytics();

  return (
    <div className="app-container" data-testid="app-container">
      <Toaster position="top-right" richColors />
      
      {/* Header */}
      <header className="app-header" data-testid="app-header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo-icon">
              <Zap className="w-6 h-6" />
            </div>
            <div>
              <h1 className="app-title">Animal Image Similarity Search</h1>
              <p className="app-subtitle">Deep Learning + FAISS Powered Visual Search</p>
            </div>
          </div>
          <div className="header-stats">
            <Badge variant="outline" className="stat-badge" data-testid="index-status-badge">
              <Database className="w-3 h-3 mr-1" />
              {datasetStats?.index_built ? `${datasetStats.index_size} indexed` : "No index"}
            </Badge>
            <Badge variant="outline" className="stat-badge">
              <Image className="w-3 h-3 mr-1" />
              {datasetStats?.total_images || 0} images
            </Badge>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="main-tabs">
          <TabsList className="tabs-list" data-testid="main-tabs">
            <TabsTrigger value="search" className="tab-trigger" data-testid="tab-search">
              <Search className="w-4 h-4 mr-2" /> Search
            </TabsTrigger>
            <TabsTrigger value="dataset" className="tab-trigger" data-testid="tab-dataset">
              <Database className="w-4 h-4 mr-2" /> Dataset
            </TabsTrigger>
            <TabsTrigger value="analytics" className="tab-trigger" data-testid="tab-analytics">
              <BarChart3 className="w-4 h-4 mr-2" /> Analytics
            </TabsTrigger>
            <TabsTrigger value="settings" className="tab-trigger" data-testid="tab-settings">
              <Settings className="w-4 h-4 mr-2" /> Settings
            </TabsTrigger>
          </TabsList>

          {/* Search Tab */}
          <TabsContent value="search" className="tab-content">
            <div className="search-layout">
              {/* Query Panel */}
              <Card className="query-card" data-testid="query-panel">
                <CardHeader>
                  <CardTitle className="card-title">Query Image</CardTitle>
                  <CardDescription>Upload an image to find similar animals</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="query-upload-area">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleQueryImageChange}
                      className="hidden"
                      id="query-image-input"
                      data-testid="query-image-input"
                    />
                    <label htmlFor="query-image-input" className="upload-label">
                      {queryPreview ? (
                        <div className="preview-container">
                          <img src={queryPreview} alt="Query" className="query-preview" />
                          <button 
                            className="clear-preview"
                            onClick={(e) => {
                              e.preventDefault();
                              setQueryImage(null);
                              setQueryPreview(null);
                            }}
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <div className="upload-placeholder">
                          <Upload className="w-10 h-10 text-muted-foreground" />
                          <span>Click to upload query image</span>
                        </div>
                      )}
                    </label>
                  </div>

                  <div className="search-controls">
                    <div className="control-group">
                      <Label>Top-K Results: {topK}</Label>
                      <Slider
                        value={[topK]}
                        onValueChange={([val]) => setTopK(val)}
                        min={1}
                        max={50}
                        step={1}
                        className="mt-2"
                        data-testid="topk-slider"
                      />
                    </div>
                    <div className="control-group">
                      <Label>Similarity Threshold: {threshold.toFixed(2)}</Label>
                      <Slider
                        value={[threshold]}
                        onValueChange={([val]) => setThreshold(val)}
                        min={0}
                        max={1}
                        step={0.01}
                        className="mt-2"
                        data-testid="threshold-slider"
                      />
                    </div>
                  </div>

                  <Button
                    onClick={handleSearch}
                    disabled={isSearching || !queryImage}
                    className="search-button"
                    data-testid="search-button"
                  >
                    {isSearching ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Searching...</>
                    ) : (
                      <><Search className="w-4 h-4 mr-2" /> Find Similar Images</>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Results Panel */}
              <Card className="results-card" data-testid="results-panel">
                <CardHeader>
                  <CardTitle className="card-title">Search Results</CardTitle>
                  {searchStats && (
                    <CardDescription>
                      Found {searchStats.resultsCount} results in {searchStats.searchTime.toFixed(2)}ms
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  {searchResults.length > 0 ? (
                    <ScrollArea className="results-scroll">
                      <div className="results-grid" data-testid="results-grid">
                        {searchResults.map((result, idx) => (
                          <div
                            key={result.image_id}
                            className="result-item"
                            onClick={() => setSelectedImage(result)}
                            data-testid={`result-item-${idx}`}
                          >
                            <div className="result-rank">#{idx + 1}</div>
                            <img
                              src={getImageUrl(result.filepath)}
                              alt={result.filename}
                              className="result-thumbnail"
                            />
                            <div className="result-info">
                              <Badge className="category-badge">{result.category}</Badge>
                              <span className="similarity-score">
                                {(result.similarity_score * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  ) : (
                    <div className="no-results">
                      <Image className="w-16 h-16 text-muted-foreground" />
                      <p>Upload a query image and click search</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Logs Panel */}
            <Card className="logs-card" data-testid="logs-panel">
              <CardHeader 
                className="logs-header cursor-pointer"
                onClick={() => setLogsExpanded(!logsExpanded)}
              >
                <div className="flex items-center justify-between">
                  <CardTitle className="card-title flex items-center">
                    <FileText className="w-4 h-4 mr-2" /> Activity Logs
                  </CardTitle>
                  {logsExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </div>
              </CardHeader>
              {logsExpanded && (
                <CardContent>
                  <ScrollArea className="logs-scroll">
                    {logs.length > 0 ? (
                      <div className="logs-list">
                        {logs.map((log, idx) => (
                          <div key={idx} className={`log-entry log-${log.level.toLowerCase()}`}>
                            <span className="log-time">
                              {new Date(log.timestamp).toLocaleTimeString()}
                            </span>
                            <Badge variant={log.level === "ERROR" ? "destructive" : "secondary"} className="log-level">
                              {log.level}
                            </Badge>
                            <span className="log-category">[{log.category}]</span>
                            <span className="log-message">{log.message}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted-foreground text-center py-4">No logs yet</p>
                    )}
                  </ScrollArea>
                  <Button variant="ghost" size="sm" onClick={handleClearLogs} className="mt-2">
                    <Trash2 className="w-3 h-3 mr-1" /> Clear Logs
                  </Button>
                </CardContent>
              )}
            </Card>
          </TabsContent>

          {/* Dataset Tab */}
          <TabsContent value="dataset" className="tab-content">
            <div className="dataset-layout">
              <Card className="upload-card" data-testid="upload-panel">
                <CardHeader>
                  <CardTitle className="card-title">Upload Images</CardTitle>
                  <CardDescription>Add images to your dataset by category</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="upload-form">
                    <div className="form-group">
                      <Label>Category</Label>
                      <Select value={uploadCategory} onValueChange={setUploadCategory}>
                        <SelectTrigger data-testid="category-select">
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent className="max-h-[300px]">
                          {sampleCategories && typeof sampleCategories === 'object' && !Array.isArray(sampleCategories) ? (
                            // Organized categories by type
                            Object.entries(sampleCategories).map(([group, cats]) => (
                              <div key={group}>
                                <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider bg-muted/50">
                                  {group.replace(/_/g, ' ')}
                                </div>
                                {Array.isArray(cats) && cats.map(cat => (
                                  <SelectItem key={cat} value={cat} className="pl-4">{cat}</SelectItem>
                                ))}
                              </div>
                            ))
                          ) : Array.isArray(sampleCategories) ? (
                            // Flat list of categories
                            sampleCategories.map(cat => (
                              <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                            ))
                          ) : null}
                          <SelectItem value="unknown">unknown</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="form-group">
                      <Label>Images</Label>
                      <Input
                        type="file"
                        accept="image/*"
                        multiple
                        onChange={(e) => setUploadFiles(Array.from(e.target.files))}
                        data-testid="dataset-upload-input"
                      />
                      {uploadFiles.length > 0 && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {uploadFiles.length} files selected
                        </p>
                      )}
                    </div>

                    <Button
                      onClick={handleUploadDataset}
                      disabled={isUploading || uploadFiles.length === 0}
                      className="w-full"
                      data-testid="upload-button"
                    >
                      {isUploading ? (
                        <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Uploading...</>
                      ) : (
                        <><Upload className="w-4 h-4 mr-2" /> Upload Images</>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card className="stats-card" data-testid="stats-panel">
                <CardHeader>
                  <CardTitle className="card-title">Dataset Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="stats-grid">
                    <div className="stat-item">
                      <span className="stat-value">{datasetStats?.total_images || 0}</span>
                      <span className="stat-label">Total Images</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">{Object.keys(datasetStats?.categories || {}).length}</span>
                      <span className="stat-label">Categories</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">{datasetStats?.index_size || 0}</span>
                      <span className="stat-label">Indexed</span>
                    </div>
                  </div>

                  {datasetStats?.categories && Object.keys(datasetStats.categories).length > 0 && (
                    <Accordion type="single" collapsible className="mt-4" defaultValue="categories">
                      <AccordionItem value="categories">
                        <AccordionTrigger>Category Distribution ({Object.keys(datasetStats.categories).length} categories)</AccordionTrigger>
                        <AccordionContent>
                          <ScrollArea className="h-[300px]">
                            <div className="category-list">
                              {/* Group categories by type */}
                              {(() => {
                                const cats = datasetStats.categories;
                                const groups = {
                                  'Mammals': ['cat', 'dog', 'lion', 'tiger', 'elephant', 'bear', 'wolf', 'fox', 'deer', 'zebra', 'giraffe', 'rabbit', 'panda', 'koala', 'horse', 'cow'],
                                  'Birds': ['eagle', 'owl', 'parrot', 'penguin', 'flamingo', 'peacock'],
                                  'Fish & Sea': ['shark', 'dolphin', 'whale', 'turtle', 'octopus', 'goldfish', 'clownfish'],
                                  'Reptiles & Amphibians': ['snake', 'lizard', 'crocodile', 'frog'],
                                  'Insects': ['butterfly', 'bee'],
                                  'Other': []
                                };
                                
                                // Get categories that don't fit in groups
                                const allGrouped = Object.values(groups).flat();
                                Object.keys(cats).forEach(cat => {
                                  if (!allGrouped.includes(cat)) {
                                    groups['Other'].push(cat);
                                  }
                                });
                                
                                return Object.entries(groups).map(([groupName, groupCats]) => {
                                  const relevantCats = groupCats.filter(c => cats[c]);
                                  if (relevantCats.length === 0) return null;
                                  
                                  return (
                                    <div key={groupName} className="mb-4">
                                      <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                                        {groupName}
                                      </h5>
                                      {relevantCats.map(cat => (
                                        <div key={cat} className="category-item">
                                          <span className="capitalize">{cat}</span>
                                          <Badge variant="outline">{cats[cat]}</Badge>
                                        </div>
                                      ))}
                                    </div>
                                  );
                                });
                              })()}
                            </div>
                          </ScrollArea>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  )}

                  <div className="index-actions">
                    <Button
                      onClick={handleBuildIndex}
                      disabled={isBuilding || (datasetStats?.total_images || 0) === 0}
                      className="build-button"
                      data-testid="build-index-button"
                    >
                      {isBuilding ? (
                        <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Building Index...</>
                      ) : (
                        <><RefreshCw className="w-4 h-4 mr-2" /> Build / Rebuild Index</>
                      )}
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={handleClearDataset}
                      data-testid="clear-dataset-button"
                    >
                      <Trash2 className="w-4 h-4 mr-2" /> Clear Dataset
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="tab-content">
            <Card data-testid="analytics-panel">
              <CardHeader>
                <CardTitle className="card-title">Search Analytics</CardTitle>
                <CardDescription>Analysis of your last search results</CardDescription>
              </CardHeader>
              <CardContent>
                {analytics ? (
                  <div className="analytics-content">
                    <div className="analytics-grid">
                      <div className="analytics-stat">
                        <span className="analytics-value">{(analytics.avgSimilarity * 100).toFixed(1)}%</span>
                        <span className="analytics-label">Average Similarity</span>
                      </div>
                      <div className="analytics-stat">
                        <span className="analytics-value">{(analytics.maxSimilarity * 100).toFixed(1)}%</span>
                        <span className="analytics-label">Max Similarity</span>
                      </div>
                      <div className="analytics-stat">
                        <span className="analytics-value">{(analytics.minSimilarity * 100).toFixed(1)}%</span>
                        <span className="analytics-label">Min Similarity</span>
                      </div>
                      <div className="analytics-stat">
                        <span className="analytics-value">{Object.keys(analytics.categoryDist).length}</span>
                        <span className="analytics-label">Categories in Results</span>
                      </div>
                    </div>

                    <div className="category-distribution">
                      <h4 className="text-sm font-medium mb-3">Category Distribution</h4>
                      <div className="distribution-bars">
                        {Object.entries(analytics.categoryDist).map(([cat, count]) => (
                          <div key={cat} className="distribution-item">
                            <div className="distribution-label">
                              <span>{cat}</span>
                              <span>{count} ({((count / searchResults.length) * 100).toFixed(0)}%)</span>
                            </div>
                            <Progress value={(count / searchResults.length) * 100} className="h-2" />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="no-analytics">
                    <BarChart3 className="w-16 h-16 text-muted-foreground" />
                    <p>Run a search to see analytics</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="tab-content">
            <Card data-testid="settings-panel">
              <CardHeader>
                <CardTitle className="card-title">Search Settings</CardTitle>
                <CardDescription>Configure search parameters</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="settings-form">
                  <div className="setting-item">
                    <Label>Default Top-K Results</Label>
                    <p className="text-sm text-muted-foreground">Number of similar images to return</p>
                    <Slider
                      value={[topK]}
                      onValueChange={([val]) => setTopK(val)}
                      min={1}
                      max={50}
                      step={1}
                      className="mt-2 max-w-md"
                    />
                    <span className="text-sm font-medium">{topK}</span>
                  </div>

                  <div className="setting-item">
                    <Label>Similarity Threshold</Label>
                    <p className="text-sm text-muted-foreground">Minimum similarity score (0-1)</p>
                    <Slider
                      value={[threshold]}
                      onValueChange={([val]) => setThreshold(val)}
                      min={0}
                      max={1}
                      step={0.01}
                      className="mt-2 max-w-md"
                    />
                    <span className="text-sm font-medium">{threshold.toFixed(2)}</span>
                  </div>

                  <div className="setting-item">
                    <Label>Feature Extraction Model</Label>
                    <p className="text-sm text-muted-foreground">ResNet50 (ImageNet pretrained)</p>
                    <Badge className="mt-2">ResNet50</Badge>
                  </div>

                  <div className="setting-item">
                    <Label>FAISS Index Type</Label>
                    <p className="text-sm text-muted-foreground">Inner Product (Cosine Similarity)</p>
                    <Badge className="mt-2">IndexFlatIP</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Image Preview Dialog */}
      <Dialog open={!!selectedImage} onOpenChange={() => setSelectedImage(null)}>
        <DialogContent className="image-dialog" data-testid="image-preview-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Eye className="w-4 h-4" /> Image Preview
            </DialogTitle>
          </DialogHeader>
          {selectedImage && (
            <div className="preview-content">
              <img
                src={getImageUrl(selectedImage.filepath)}
                alt={selectedImage.filename}
                className="preview-image"
              />
              <div className="preview-details">
                <div className="detail-row">
                  <span className="detail-label">Filename:</span>
                  <span>{selectedImage.filename}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Category:</span>
                  <Badge>{selectedImage.category}</Badge>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Similarity:</span>
                  <span className="text-lg font-bold text-primary">
                    {(selectedImage.similarity_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;
