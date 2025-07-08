import requests
import os
import json
import time
from pathlib import Path

# Base URL for the API
BASE_URL = "http://localhost:8001"

def test_file_upload_corrupted_pdf():
    """Test the file upload endpoint with a corrupted PDF file"""
    print("\n=== Testing File Upload (Corrupted PDF) ===")
    
    # Create a corrupted PDF file for testing
    corrupted_pdf_path = "/app/corrupted.pdf"
    with open(corrupted_pdf_path, "w") as f:
        f.write("%PDF-1.5\nThis is not a valid PDF file structure.")
    
    # Upload the file
    with open(corrupted_pdf_path, "rb") as f:
        files = {"file": ("corrupted.pdf", f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/api/upload", files=files)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Response: {response.text}")
    
    return response

if __name__ == "__main__":
    test_file_upload_corrupted_pdf()