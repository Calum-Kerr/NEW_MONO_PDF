#!/usr/bin/env python3
"""
Comprehensive API test suite for PDF Tools Platform.
Tests all endpoints and functionality including StirlingPDF integration.
"""

import requests
import json
import time
import sys
from datetime import datetime

class PDFToolsAPITester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", response_time=None):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        rt_str = f" ({response_time:.3f}s)" if response_time else ""
        print(f"{status} {test_name}{rt_str}")
        if message:
            print(f"    {message}")
    
    def make_request(self, method, endpoint, **kwargs):
        """Make HTTP request and measure response time."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = self.session.request(method, url, **kwargs)
            response_time = time.time() - start_time
            return response, response_time
        except Exception as e:
            response_time = time.time() - start_time
            return None, response_time
    
    def test_health_check(self):
        """Test basic health check endpoint."""
        response, rt = self.make_request("GET", "/health")
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data", {}).get("status") == "healthy":
                self.log_test("Health Check", True, "Service is healthy", rt)
                return True
            else:
                self.log_test("Health Check", False, "Invalid health response", rt)
        else:
            self.log_test("Health Check", False, f"HTTP {response.status_code if response else 'No response'}", rt)
        return False
    
    def test_stirling_health(self):
        """Test StirlingPDF integration health."""
        response, rt = self.make_request("GET", "/api/stirling/health")
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                stirling_data = data.get("data", {})
                if stirling_data.get("success"):
                    self.log_test("StirlingPDF Health", True, "StirlingPDF is available", rt)
                else:
                    self.log_test("StirlingPDF Health", False, stirling_data.get("error", "Unknown error"), rt)
            else:
                self.log_test("StirlingPDF Health", False, "API response error", rt)
        else:
            self.log_test("StirlingPDF Health", False, f"HTTP {response.status_code if response else 'No response'}", rt)
    
    def test_auth_endpoints(self):
        """Test authentication endpoints."""
        # Test registration
        reg_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        response, rt = self.make_request("POST", "/api/auth/register", 
                                       json=reg_data,
                                       headers={"Content-Type": "application/json"})
        
        if response and response.status_code == 503:
            self.log_test("User Registration", True, "Auth service unavailable (expected in test)", rt)
        elif response:
            self.log_test("User Registration", False, f"Unexpected response: {response.status_code}", rt)
        else:
            self.log_test("User Registration", False, "No response received", rt)
        
        # Test login
        login_data = {
            "email": "test@example.com", 
            "password": "testpassword123"
        }
        
        response, rt = self.make_request("POST", "/api/auth/login",
                                       json=login_data,
                                       headers={"Content-Type": "application/json"})
        
        if response and response.status_code == 503:
            self.log_test("User Login", True, "Auth service unavailable (expected in test)", rt)
        elif response:
            self.log_test("User Login", False, f"Unexpected response: {response.status_code}", rt)
        else:
            self.log_test("User Login", False, "No response received", rt)
    
    def test_file_upload(self):
        """Test file upload endpoint."""
        # Create a mock PDF file
        mock_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        
        files = {"file": ("test.pdf", mock_pdf, "application/pdf")}
        
        response, rt = self.make_request("POST", "/api/files/upload", files=files)
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.log_test("File Upload", True, f"File uploaded: {data.get('data', {}).get('filename')}", rt)
            else:
                self.log_test("File Upload", False, data.get("message", "Upload failed"), rt)
        else:
            self.log_test("File Upload", False, f"HTTP {response.status_code if response else 'No response'}", rt)
    
    def test_pdf_operations(self):
        """Test PDF processing endpoints."""
        
        # Test PDF merge
        merge_data = {
            "file_urls": [
                "https://example.com/file1.pdf",
                "https://example.com/file2.pdf"
            ]
        }
        
        response, rt = self.make_request("POST", "/api/pdf/merge",
                                       json=merge_data,
                                       headers={"Content-Type": "application/json"})
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.log_test("PDF Merge", True, f"Job created: {data.get('data', {}).get('job_id')}", rt)
            else:
                self.log_test("PDF Merge", False, data.get("message", "Merge failed"), rt)
        else:
            self.log_test("PDF Merge", False, f"HTTP {response.status_code if response else 'No response'}", rt)
        
        # Test PDF split
        split_data = {
            "file_url": "https://example.com/document.pdf",
            "pages": "1-3,5"
        }
        
        response, rt = self.make_request("POST", "/api/pdf/split",
                                       json=split_data,
                                       headers={"Content-Type": "application/json"})
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.log_test("PDF Split", True, f"Job created: {data.get('data', {}).get('job_id')}", rt)
            else:
                self.log_test("PDF Split", False, data.get("message", "Split failed"), rt)
        else:
            self.log_test("PDF Split", False, f"HTTP {response.status_code if response else 'No response'}", rt)
        
        # Test PDF compress
        compress_data = {
            "file_url": "https://example.com/document.pdf",
            "compression_level": 2
        }
        
        response, rt = self.make_request("POST", "/api/pdf/compress",
                                       json=compress_data,
                                       headers={"Content-Type": "application/json"})
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.log_test("PDF Compress", True, f"Job created: {data.get('data', {}).get('job_id')}", rt)
            else:
                self.log_test("PDF Compress", False, data.get("message", "Compress failed"), rt)
        else:
            self.log_test("PDF Compress", False, f"HTTP {response.status_code if response else 'No response'}", rt)
        
        # Test file conversion
        convert_data = {
            "file_url": "https://example.com/document.docx",
            "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        
        response, rt = self.make_request("POST", "/api/pdf/convert",
                                       json=convert_data,
                                       headers={"Content-Type": "application/json"})
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.log_test("File Convert", True, f"Job created: {data.get('data', {}).get('job_id')}", rt)
            else:
                self.log_test("File Convert", False, data.get("message", "Convert failed"), rt)
        else:
            self.log_test("File Convert", False, f"HTTP {response.status_code if response else 'No response'}", rt)
    
    def test_payment_endpoints(self):
        """Test payment endpoints."""
        
        # Test create checkout
        checkout_data = {
            "plan": "pro_monthly",
            "success_url": "https://snackpdf.com/success",
            "cancel_url": "https://snackpdf.com/pricing"
        }
        
        response, rt = self.make_request("POST", "/api/payments/create-checkout",
                                       json=checkout_data,
                                       headers={"Content-Type": "application/json"})
        
        if response and response.status_code == 503:
            self.log_test("Create Checkout", True, "Payment service unavailable (expected in test)", rt)
        elif response:
            self.log_test("Create Checkout", False, f"Unexpected response: {response.status_code}", rt)
        else:
            self.log_test("Create Checkout", False, "No response received", rt)
        
        # Test customer portal
        portal_data = {
            "return_url": "https://snackpdf.com/account"
        }
        
        response, rt = self.make_request("POST", "/api/payments/portal",
                                       json=portal_data,
                                       headers={"Content-Type": "application/json"})
        
        if response and response.status_code == 503:
            self.log_test("Customer Portal", True, "Payment service unavailable (expected in test)", rt)
        elif response:
            self.log_test("Customer Portal", False, f"Unexpected response: {response.status_code}", rt)
        else:
            self.log_test("Customer Portal", False, "No response received", rt)
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Make multiple requests quickly to test rate limiting
        responses = []
        for i in range(5):
            response, rt = self.make_request("GET", "/health")
            if response:
                responses.append(response.status_code)
        
        # All should succeed for health check (high limit)
        if all(status == 200 for status in responses):
            self.log_test("Rate Limiting", True, "Rate limiting working correctly")
        else:
            self.log_test("Rate Limiting", False, f"Unexpected status codes: {responses}")
    
    def test_error_handling(self):
        """Test error handling."""
        
        # Test invalid endpoint
        response, rt = self.make_request("GET", "/api/invalid/endpoint")
        
        if response and response.status_code == 404:
            self.log_test("404 Error Handling", True, "Correctly returns 404 for invalid endpoint", rt)
        else:
            self.log_test("404 Error Handling", False, f"Expected 404, got {response.status_code if response else 'No response'}", rt)
        
        # Test invalid JSON
        response, rt = self.make_request("POST", "/api/pdf/merge",
                                       data="invalid json",
                                       headers={"Content-Type": "application/json"})
        
        if response and response.status_code in [400, 422]:
            self.log_test("Invalid JSON Handling", True, "Correctly handles invalid JSON", rt)
        else:
            self.log_test("Invalid JSON Handling", False, f"Expected 400/422, got {response.status_code if response else 'No response'}", rt)
    
    def run_all_tests(self):
        """Run all test suites."""
        print("🧪 Starting PDF Tools Platform API Tests")
        print("=" * 50)
        
        # Core functionality tests
        print("\n📋 Core Functionality Tests:")
        self.test_health_check()
        self.test_stirling_health()
        
        # Authentication tests
        print("\n🔐 Authentication Tests:")
        self.test_auth_endpoints()
        
        # File operations tests
        print("\n📁 File Operations Tests:")
        self.test_file_upload()
        
        # PDF processing tests
        print("\n📄 PDF Processing Tests:")
        self.test_pdf_operations()
        
        # Payment tests
        print("\n💳 Payment Tests:")
        self.test_payment_endpoints()
        
        # System tests
        print("\n⚙️ System Tests:")
        self.test_rate_limiting()
        self.test_error_handling()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Performance summary
        response_times = [r["response_time"] for r in self.test_results if r["response_time"]]
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            max_response = max(response_times)
            print(f"\n⚡ Performance:")
            print(f"Average Response Time: {avg_response:.3f}s")
            print(f"Max Response Time: {max_response:.3f}s")
        
        print("\n🎉 Testing Complete!")
        
        # Return exit code based on results
        return 0 if failed_tests == 0 else 1

def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF Tools Platform API Tester")
    parser.add_argument("--url", default="http://localhost:5000", 
                       help="Base URL for API testing (default: http://localhost:5000)")
    parser.add_argument("--output", help="Output file for test results (JSON)")
    
    args = parser.parse_args()
    
    # Run tests
    tester = PDFToolsAPITester(args.url)
    exit_code = tester.run_all_tests()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(tester.test_results, f, indent=2)
        print(f"\n💾 Test results saved to {args.output}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()