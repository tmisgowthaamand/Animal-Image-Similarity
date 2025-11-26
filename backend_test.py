#!/usr/bin/env python3
"""
Animal Image Similarity Search - Backend API Testing
Tests all backend endpoints for functionality and integration
"""

import requests
import sys
import json
import os
from datetime import datetime
from pathlib import Path
import time

class AnimalSearchAPITester:
    def __init__(self, base_url="https://species-explorer-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test("API Root", success, 
                         f"Status: {response.status_code}", data)
            return success
        except Exception as e:
            self.log_test("API Root", False, str(e))
            return False

    def test_dataset_stats(self):
        """Test GET /api/dataset-stats"""
        try:
            response = requests.get(f"{self.api_url}/dataset-stats", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['total_images', 'categories', 'index_built', 'index_size']
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing fields: {missing_fields}"
                else:
                    details = f"Total images: {data['total_images']}, Categories: {len(data['categories'])}, Index built: {data['index_built']}"
                
                self.log_test("Dataset Stats", success, details, data)
            else:
                self.log_test("Dataset Stats", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Dataset Stats", False, str(e))
            return False

    def test_categories(self):
        """Test GET /api/categories"""
        try:
            response = requests.get(f"{self.api_url}/categories", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                categories = data.get('categories', [])
                details = f"Found {len(categories)} categories: {categories}"
                self.log_test("Categories", success, details, data)
            else:
                self.log_test("Categories", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Categories", False, str(e))
            return False

    def test_sample_categories(self):
        """Test GET /api/sample-categories"""
        try:
            response = requests.get(f"{self.api_url}/sample-categories", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                categories = data.get('categories', [])
                expected_categories = ['lion', 'tiger', 'elephant', 'cat', 'dog']
                found_expected = [cat for cat in expected_categories if cat in categories]
                details = f"Found {len(categories)} sample categories, {len(found_expected)} expected ones"
                self.log_test("Sample Categories", success, details, data)
            else:
                self.log_test("Sample Categories", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Sample Categories", False, str(e))
            return False

    def test_logs(self):
        """Test GET /api/logs"""
        try:
            response = requests.get(f"{self.api_url}/logs?limit=10", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Retrieved {len(data)} log entries"
                self.log_test("Get Logs", success, details, {"log_count": len(data)})
            else:
                self.log_test("Get Logs", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Get Logs", False, str(e))
            return False

    def test_clear_logs(self):
        """Test DELETE /api/clear-logs"""
        try:
            response = requests.delete(f"{self.api_url}/clear-logs", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Response: {data.get('message', 'Logs cleared')}"
                self.log_test("Clear Logs", success, details, data)
            else:
                self.log_test("Clear Logs", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Clear Logs", False, str(e))
            return False

    def test_upload_dataset(self):
        """Test POST /api/upload-dataset with a test image"""
        try:
            # Create a simple test image file (1x1 pixel PNG)
            test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
            
            files = {'files': ('test_image.png', test_image_data, 'image/png')}
            data = {'category': 'test_category'}
            
            response = requests.post(f"{self.api_url}/upload-dataset", 
                                   files=files, data=data, timeout=15)
            success = response.status_code == 200
            
            if success:
                resp_data = response.json()
                uploaded_count = resp_data.get('uploaded', 0)
                details = f"Uploaded {uploaded_count} images to test_category"
                self.log_test("Upload Dataset", success, details, resp_data)
            else:
                self.log_test("Upload Dataset", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Upload Dataset", False, str(e))
            return False

    def test_build_index(self):
        """Test POST /api/build-index"""
        try:
            print("Building index (this may take a moment)...")
            response = requests.post(f"{self.api_url}/build-index", timeout=60)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Response: {data.get('message', 'Index built')}"
                self.log_test("Build Index", success, details, data)
            else:
                self.log_test("Build Index", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Build Index", False, str(e))
            return False

    def test_search(self):
        """Test POST /api/search with a test image"""
        try:
            # Create a simple test image file (1x1 pixel PNG)
            test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```bPPP\x00\x02\xac\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
            
            files = {'file': ('query_image.png', test_image_data, 'image/png')}
            data = {'top_k': 5, 'threshold': 0.0}
            
            print("Performing search (this may take a moment)...")
            response = requests.post(f"{self.api_url}/search", 
                                   files=files, data=data, timeout=30)
            success = response.status_code == 200
            
            if success:
                resp_data = response.json()
                results_count = len(resp_data.get('results', []))
                search_time = resp_data.get('search_time_ms', 0)
                total_indexed = resp_data.get('total_indexed', 0)
                details = f"Found {results_count} results in {search_time:.2f}ms, {total_indexed} images indexed"
                self.log_test("Search Images", success, details, 
                             {"results_count": results_count, "search_time_ms": search_time})
            else:
                error_msg = response.text if response.status_code != 200 else f"Status: {response.status_code}"
                self.log_test("Search Images", False, error_msg)
            
            return success
        except Exception as e:
            self.log_test("Search Images", False, str(e))
            return False

    def run_comprehensive_test(self):
        """Run all API tests in sequence"""
        print("🚀 Starting Animal Image Similarity Search API Tests")
        print(f"🔗 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_api_root():
            print("❌ API root test failed - stopping tests")
            return False
        
        # Test read-only endpoints
        self.test_dataset_stats()
        self.test_categories()
        self.test_sample_categories()
        self.test_logs()
        
        # Test write operations
        self.test_clear_logs()
        self.test_upload_dataset()
        
        # Test index building (may take time)
        self.test_build_index()
        
        # Test search functionality
        self.test_search()
        
        # Final summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    """Main test execution"""
    tester = AnimalSearchAPITester()
    
    try:
        success = tester.run_comprehensive_test()
        
        # Save detailed results
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
            "test_details": tester.test_results
        }
        
        with open("/app/backend_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())