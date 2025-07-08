import requests
import os
import json
import time
from pathlib import Path
import random
import string

# Base URL for the API
BASE_URL = "http://localhost:8001"

# Test file paths
TEST_PDF_PATH = "/app/test_table.pdf"
TEST_PDF_PATH_2 = "/app/test_pdf.pdf"

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
    """Test the file upload endpoint with a valid PDF"""
    print("\n=== Testing File Upload (Valid PDF) ===")
    
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

def test_file_upload_non_pdf():
    """Test the file upload endpoint with a non-PDF file"""
    print("\n=== Testing File Upload (Non-PDF) ===")
    
    # Create a text file for testing
    test_txt_path = "/app/test_file.txt"
    with open(test_txt_path, "w") as f:
        f.write("This is a test file, not a PDF.")
    
    # Upload the file
    with open(test_txt_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json() if response.status_code == 200 else response.text}")
    
    # Should return an error for non-PDF files
    assert response.status_code == 400
    print("✅ Non-PDF file upload test passed (rejected as expected)")
    return True

def test_file_upload_corrupted_pdf():
    """Test the file upload endpoint with a corrupted PDF file"""
    print("\n=== Testing File Upload (Corrupted PDF) ===")
    
    # Create a corrupted PDF file for testing
    corrupted_pdf_path = "/app/corrupted.pdf"
    with open(corrupted_pdf_path, "w") as f:
        f.write("%PDF-1.5\nThis is not a valid PDF file structure.")
    
    # Upload the file
    with open(corrupted_pdf_path, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json() if response.status_code == 200 else response.text}")
    
    # Should return an error for corrupted PDF files
    assert response.status_code == 400
    print("✅ Corrupted PDF file upload test passed (rejected as expected)")
    return True

def test_file_upload_large_pdf():
    """Test the file upload endpoint with a large PDF file"""
    print("\n=== Testing File Upload (Large PDF) ===")
    
    # Check if second test file exists (assuming it's larger)
    if os.path.exists(TEST_PDF_PATH_2):
        with open(TEST_PDF_PATH_2, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code == 200 else response.text}")
        
        assert response.status_code == 200
        print("✅ Large PDF file upload test passed")
        return True
    else:
        # Create a larger PDF-like file for testing
        large_pdf_path = "/app/large_test.pdf"
        with open(large_pdf_path, "wb") as f:
            # Write PDF header
            f.write(b"%PDF-1.5\n")
            # Write 1MB of random data
            f.write(os.urandom(1024 * 1024))
            # Write PDF footer
            f.write(b"\n%%EOF")
        
        # Upload the file
        with open(large_pdf_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{BASE_URL}/api/upload", files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code == 200 else response.text}")
        
        # This might pass or fail depending on server configuration
        print(f"{'✅' if response.status_code == 200 else '❌'} Large PDF file upload test {'passed' if response.status_code == 200 else 'failed'}")
        return response.status_code == 200

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

def test_file_info_invalid_id():
    """Test the file info endpoint with an invalid file ID"""
    print("\n=== Testing File Info (Invalid ID) ===")
    
    invalid_id = "invalid-file-id-12345"
    response = requests.get(f"{BASE_URL}/api/files/{invalid_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    assert response.status_code == 404
    print("✅ Invalid file ID test passed (404 as expected)")
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

def test_pdf_download_invalid_id():
    """Test the PDF download endpoint with an invalid file ID"""
    print("\n=== Testing PDF Download (Invalid ID) ===")
    
    invalid_id = "invalid-file-id-12345"
    response = requests.get(f"{BASE_URL}/api/files/{invalid_id}/pdf")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    assert response.status_code == 404
    print("✅ Invalid file ID PDF download test passed (404 as expected)")
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

def test_table_extraction_invalid_file_id():
    """Test the table extraction endpoint with an invalid file ID"""
    print("\n=== Testing Table Extraction (Invalid File ID) ===")
    
    # Define a selection area
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
    
    # Prepare form data with invalid file_id
    form_data = {
        "file_id": "invalid-file-id-12345",
        "selections": json.dumps(selections)
    }
    
    response = requests.post(f"{BASE_URL}/api/extract", data=form_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    assert response.status_code == 404
    print("✅ Invalid file ID table extraction test passed (404 as expected)")
    return True

def test_table_extraction_invalid_selections():
    """Test the table extraction endpoint with invalid selections"""
    print("\n=== Testing Table Extraction (Invalid Selections) ===")
    
    if not test_data["file_id"]:
        print("❌ No file_id available. Run file upload test first.")
        return False
    
    # Prepare form data with invalid selections
    form_data = {
        "file_id": test_data["file_id"],
        "selections": "not-a-valid-json"
    }
    
    response = requests.post(f"{BASE_URL}/api/extract", data=form_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    assert response.status_code == 500  # Expecting server error for invalid JSON
    print("✅ Invalid selections table extraction test passed (error as expected)")
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

def test_job_status_invalid_id():
    """Test the job status endpoint with an invalid job ID"""
    print("\n=== Testing Job Status (Invalid ID) ===")
    
    invalid_id = "invalid-job-id-12345"
    response = requests.get(f"{BASE_URL}/api/jobs/{invalid_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    assert response.status_code == 404
    print("✅ Invalid job ID test passed (404 as expected)")
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

def test_csv_download_invalid_id():
    """Test the CSV download endpoint with an invalid job ID"""
    print("\n=== Testing CSV Download (Invalid ID) ===")
    
    invalid_id = "invalid-job-id-12345"
    response = requests.get(f"{BASE_URL}/api/jobs/{invalid_id}/download")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    assert response.status_code == 404
    print("✅ Invalid job ID CSV download test passed (404 as expected)")
    return True

def run_all_tests():
    """Run all tests in sequence"""
    print("\n🔍 Starting Enhanced Backend API Tests 🔍")
    
    # Basic functionality tests
    test_health_check()
    
    # File upload tests with different scenarios
    test_file_upload()
    test_file_upload_non_pdf()
    test_file_upload_corrupted_pdf()
    test_file_upload_large_pdf()
    
    # File info tests
    test_file_info()
    test_file_info_invalid_id()
    
    # PDF download tests
    test_pdf_download()
    test_pdf_download_invalid_id()
    
    # Table extraction tests
    test_table_extraction()
    test_table_extraction_invalid_file_id()
    test_table_extraction_invalid_selections()
    
    # Job status tests
    test_job_status()
    test_job_status_invalid_id()
    
    # CSV download tests
    test_csv_download()
    test_csv_download_invalid_id()
    
    print("\n✨ All tests completed ✨")

if __name__ == "__main__":
    run_all_tests()