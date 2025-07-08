import requests
import uuid

# Base URL for the API
BASE_URL = "http://localhost:8001"

def test_file_info_invalid_id():
    """Test the file info endpoint with an invalid file ID"""
    print("\n=== Testing File Info (Invalid ID) ===")
    
    invalid_id = str(uuid.uuid4())  # Generate a random UUID that doesn't exist
    response = requests.get(f"{BASE_URL}/api/files/{invalid_id}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response

if __name__ == "__main__":
    test_file_info_invalid_id()