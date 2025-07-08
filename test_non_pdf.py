import requests
import os
import json
import time
from pathlib import Path

# Base URL for the API
BASE_URL = "http://localhost:8001"

def test_file_upload_non_pdf():
    """Test the file upload endpoint with a non-PDF file"""
    print("\n=== Testing File Upload (Non-PDF) ===")
    
    # Create a text file for testing
    test_txt_path = "/app/test_file.txt"
    with open(test_txt_path, "w") as f:
        f.write("This is a test file, not a PDF.")
    
    # Upload the file
    with open(test_txt_path, "rb") as f:
        files = {"file": (f.name, f, "text/plain")}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Response: {response.text}")
    
    return response

if __name__ == "__main__":
    test_file_upload_non_pdf()