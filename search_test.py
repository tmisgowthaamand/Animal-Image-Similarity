#!/usr/bin/env python3
"""
Test search functionality with real dog image from dataset
"""

import requests
import json

def test_search_with_real_image():
    """Test search with actual dog image from dataset"""
    api_url = "https://species-explorer-2.preview.emergentagent.com/api"
    
    print("🔍 Testing search with real dog image from dataset...")
    
    try:
        # Read a local dog image from the dataset
        with open('/app/backend/uploads/dataset/dog/dog3.jpg', 'rb') as f:
            image_data = f.read()
        
        files = {'file': ('dog3.jpg', image_data, 'image/jpeg')}
        data = {'top_k': 10, 'threshold': 0.0}
        
        response = requests.post(f"{api_url}/search", files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Search successful!")
            print(f"📊 Query image: {result['query_image']}")
            print(f"🔢 Results found: {len(result['results'])}")
            print(f"⏱️  Search time: {result['search_time_ms']:.2f}ms")
            print(f"📈 Total indexed: {result['total_indexed']}")
            
            print("\n🎯 Top results:")
            for i, res in enumerate(result['results'][:5]):
                print(f"  {i+1}. {res['filename']} (category: {res['category']}, score: {res['similarity_score']:.4f})")
            
            # Check if we found dog images in results
            dog_results = [r for r in result['results'] if r['category'] == 'dog']
            print(f"\n🐕 Found {len(dog_results)} dog images in results")
            
            return True
        else:
            print(f"❌ Search failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False

if __name__ == "__main__":
    test_search_with_real_image()