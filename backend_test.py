import requests
import os
import json
import time
from pathlib import Path

# Base URL for the API
BASE_URL = "http://localhost:8001"

# Test file path
TEST_PDF_PATH = "/app/test_table.pdf"

# Store test data
test_data = {
    "file_id": None,
    "job_id": None
}

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    print("✅ Health check test passed")

def test_file_upload():
    """Test the file upload endpoint"""
    print("\n=== Testing File Upload ===")
    
    # Check if test file exists
    if not os.path.exists(TEST_PDF_PATH):
        print(f"❌ Test file not found: {TEST_PDF_PATH}")
        return False
    
    # Upload the file
    with open(TEST_PDF_PATH, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert "file_id" in response.json()
    assert "filename" in response.json()
    assert "total_pages" in response.json()
    assert "file_size" in response.json()
    
    # Store file_id for later tests
    test_data["file_id"] = response.json()["file_id"]
    print(f"✅ File upload test passed. File ID: {test_data['file_id']}")
    return True

def test_file_info():
    """Test the file info endpoint"""
    print("\n=== Testing File Info ===")
    
    if not test_data["file_id"]:
        print("❌ No file_id available. Run file upload test first.")
        return False
    
    response = requests.get(f"{BASE_URL}/api/files/{test_data['file_id']}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json()["file_id"] == test_data["file_id"]
    print("✅ File info test passed")
    return True

def test_pdf_download():
    """Test the PDF download endpoint"""
    print("\n=== Testing PDF Download ===")
    
    if not test_data["file_id"]:
        print("❌ No file_id available. Run file upload test first.")
        return False
    
    response = requests.get(f"{BASE_URL}/api/files/{test_data['file_id']}/pdf")
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.headers.get('Content-Type')}")
    print(f"Content Length: {len(response.content)} bytes")
    
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/pdf"
    assert len(response.content) > 0
    
    # Save the downloaded PDF for verification
    download_path = "/app/downloaded_test.pdf"
    with open(download_path, "wb") as f:
        f.write(response.content)
    
    print(f"✅ PDF download test passed. Saved to: {download_path}")
    return True

def test_table_extraction():
    """Test the table extraction endpoint"""
    print("\n=== Testing Table Extraction ===")
    
    if not test_data["file_id"]:
        print("❌ No file_id available. Run file upload test first.")
        return False
    
    # Define a selection area (adjust these values based on your test PDF)
    selections = [
        {
            "page": 0,
            "x1": 50,
            "y1": 50,
            "x2": 500,
            "y2": 200,
            "width": 450,
            "height": 150
        }
    ]
    
    # Prepare form data
    form_data = {
        "file_id": test_data["file_id"],
        "selections": json.dumps(selections)
    }
    
    response = requests.post(f"{BASE_URL}/api/extract", data=form_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert "job_id" in response.json()
    assert "status" in response.json()
    assert "csv_data" in response.json()
    
    # Store job_id for later tests
    test_data["job_id"] = response.json()["job_id"]
    print(f"✅ Table extraction test passed. Job ID: {test_data['job_id']}")
    print(f"CSV Data Preview: {response.json()['csv_data'][:200]}...")
    return True

def test_job_status():
    """Test the job status endpoint"""
    print("\n=== Testing Job Status ===")
    
    if not test_data["job_id"]:
        print("❌ No job_id available. Run table extraction test first.")
        return False
    
    response = requests.get(f"{BASE_URL}/api/jobs/{test_data['job_id']}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json()["job_id"] == test_data["job_id"]
    assert response.json()["file_id"] == test_data["file_id"]
    assert "status" in response.json()
    assert "csv_data" in response.json()
    
    print("✅ Job status test passed")
    return True

def test_csv_download():
    """Test the CSV download endpoint"""
    print("\n=== Testing CSV Download ===")
    
    if not test_data["job_id"]:
        print("❌ No job_id available. Run table extraction test first.")
        return False
    
    response = requests.get(f"{BASE_URL}/api/jobs/{test_data['job_id']}/download")
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.headers.get('Content-Type')}")
    print(f"Content Length: {len(response.content)} bytes")
    
    assert response.status_code == 200
    # Check if Content-Type contains 'csv' (could be 'text/csv' or 'application/csv')
    assert 'csv' in response.headers.get("Content-Type", "").lower()
    assert len(response.content) > 0
    
    # Save the downloaded CSV for verification
    download_path = "/app/extracted_data.csv"
    with open(download_path, "wb") as f:
        f.write(response.content)
    
    # Print the CSV content
    print(f"CSV Content Preview: {response.content[:200]}...")
    print(f"✅ CSV download test passed. Saved to: {download_path}")
    return True

def run_all_tests():
    """Run all tests in sequence"""
    print("\n🔍 Starting Backend API Tests 🔍")
    
    # Run tests in sequence
    test_health_check()
    
    if test_file_upload():
        test_file_info()
        test_pdf_download()
        
        if test_table_extraction():
            test_job_status()
            test_csv_download()
    
    print("\n✨ All tests completed ✨")

if __name__ == "__main__":
    run_all_tests()