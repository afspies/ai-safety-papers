import requests
import time
import sys

def test_api_performance():
    """Test the API performance with caching."""
    base_url = "http://localhost:8000/api"
    
    # Test papers endpoint
    print("Testing /api/papers endpoint...")
    
    # First request (should be a cache miss)
    start_time = time.time()
    response = requests.get(f"{base_url}/papers")
    first_request_time = time.time() - start_time
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    papers = response.json()
    print(f"First request: {first_request_time:.2f} seconds, {len(papers)} papers")
    
    # Second request (should be a cache hit)
    start_time = time.time()
    response = requests.get(f"{base_url}/papers")
    second_request_time = time.time() - start_time
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    papers = response.json()
    print(f"Second request: {second_request_time:.2f} seconds, {len(papers)} papers")
    
    # Test highlighted papers endpoint
    print("\nTesting /api/papers/highlighted endpoint...")
    
    # First request (might be a cache miss)
    start_time = time.time()
    response = requests.get(f"{base_url}/papers/highlighted")
    first_request_time = time.time() - start_time
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    papers = response.json()
    print(f"First request: {first_request_time:.2f} seconds, {len(papers)} papers")
    
    # Second request (should be a cache hit)
    start_time = time.time()
    response = requests.get(f"{base_url}/papers/highlighted")
    second_request_time = time.time() - start_time
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    papers = response.json()
    print(f"Second request: {second_request_time:.2f} seconds, {len(papers)} papers")
    
    # Test paper detail endpoint with the first paper
    if papers:
        paper_id = papers[0]["uid"]
        print(f"\nTesting /api/papers/{paper_id} endpoint...")
        
        # First request (might be a cache miss)
        start_time = time.time()
        response = requests.get(f"{base_url}/papers/{paper_id}")
        first_request_time = time.time() - start_time
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return
        
        paper = response.json()
        print(f"First request: {first_request_time:.2f} seconds")
        
        # Second request (should be a cache hit)
        start_time = time.time()
        response = requests.get(f"{base_url}/papers/{paper_id}")
        second_request_time = time.time() - start_time
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return
        
        paper = response.json()
        print(f"Second request: {second_request_time:.2f} seconds")

if __name__ == "__main__":
    test_api_performance()