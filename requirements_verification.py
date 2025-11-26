#!/usr/bin/env python3
"""
Verify specific requirements from the review request
"""

import requests
import json

def verify_requirements():
    """Verify all specific requirements from the review request"""
    api_url = "https://species-explorer-2.preview.emergentagent.com/api"
    
    print("🔍 Verifying specific requirements from review request...")
    print("=" * 60)
    
    all_passed = True
    
    # 1. GET /api/dataset-stats - Should return 26 total_images with specific categories
    print("1️⃣  Testing GET /api/dataset-stats")
    try:
        response = requests.get(f"{api_url}/dataset-stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            total_images = data.get('total_images', 0)
            categories = data.get('categories', {})
            
            print(f"   ✅ Status: 200 OK")
            print(f"   📊 Total images: {total_images}")
            print(f"   📂 Categories: {categories}")
            
            # Check specific requirements
            expected_total = 26
            expected_categories = {
                'cat': 5, 'dog': 5, 'elephant': 5, 
                'lion': 5, 'tiger': 5, 'test_category': 1
            }
            
            if total_images >= expected_total:
                print(f"   ✅ Total images requirement met: {total_images} >= {expected_total}")
            else:
                print(f"   ❌ Total images requirement failed: {total_images} < {expected_total}")
                all_passed = False
            
            for cat, expected_count in expected_categories.items():
                actual_count = categories.get(cat, 0)
                if actual_count >= expected_count:
                    print(f"   ✅ Category '{cat}': {actual_count} >= {expected_count}")
                else:
                    print(f"   ❌ Category '{cat}': {actual_count} < {expected_count}")
                    all_passed = False
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_passed = False
    
    print()
    
    # 2. GET /api/categories - Should return the list of categories
    print("2️⃣  Testing GET /api/categories")
    try:
        response = requests.get(f"{api_url}/categories", timeout=10)
        if response.status_code == 200:
            data = response.json()
            categories = data.get('categories', [])
            print(f"   ✅ Status: 200 OK")
            print(f"   📂 Categories returned: {categories}")
            
            expected_cats = ['cat', 'dog', 'elephant', 'lion', 'tiger']
            found_expected = [cat for cat in expected_cats if cat in categories]
            print(f"   ✅ Expected categories found: {found_expected}")
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_passed = False
    
    print()
    
    # 3. POST /api/search - Upload an image file and search for similar images
    print("3️⃣  Testing POST /api/search")
    try:
        # Use a local dog image for testing
        with open('/app/backend/uploads/dataset/dog/dog3.jpg', 'rb') as f:
            image_data = f.read()
        
        files = {'file': ('dog3.jpg', image_data, 'image/jpeg')}
        data = {'top_k': 10, 'threshold': 0.0}
        
        response = requests.post(f"{api_url}/search", files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            results_count = len(result.get('results', []))
            search_time = result.get('search_time_ms', 0)
            total_indexed = result.get('total_indexed', 0)
            
            print(f"   ✅ Status: 200 OK")
            print(f"   🔍 Results found: {results_count}")
            print(f"   ⏱️  Search time: {search_time:.2f}ms")
            print(f"   📈 Total indexed: {total_indexed}")
            
            # Verify multipart form data parameters work
            if results_count > 0:
                print(f"   ✅ Search returned results successfully")
            else:
                print(f"   ❌ Search returned no results")
                all_passed = False
                
            if total_indexed >= 26:
                print(f"   ✅ Index has sufficient images: {total_indexed}")
            else:
                print(f"   ❌ Index has insufficient images: {total_indexed}")
                all_passed = False
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            all_passed = False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_passed = False
    
    print()
    
    # 4. GET /api/logs - Should return activity logs
    print("4️⃣  Testing GET /api/logs")
    try:
        response = requests.get(f"{api_url}/logs", timeout=10)
        if response.status_code == 200:
            logs = response.json()
            print(f"   ✅ Status: 200 OK")
            print(f"   📝 Log entries returned: {len(logs)}")
            
            if len(logs) > 0:
                print(f"   ✅ Activity logs are being recorded")
                # Show sample log entry
                if logs:
                    sample_log = logs[0]
                    print(f"   📄 Sample log: {sample_log.get('message', 'N/A')}")
            else:
                print(f"   ⚠️  No log entries found (may be expected if logs were cleared)")
        else:
            print(f"   ❌ Failed with status: {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        all_passed = False
    
    print()
    print("=" * 60)
    
    if all_passed:
        print("🎉 ALL REQUIREMENTS VERIFIED SUCCESSFULLY!")
        return True
    else:
        print("⚠️  SOME REQUIREMENTS FAILED VERIFICATION")
        return False

if __name__ == "__main__":
    success = verify_requirements()
    exit(0 if success else 1)