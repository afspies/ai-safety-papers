#!/usr/bin/env python3
import requests
import json

def test_api():
    # Base URL
    base_url = 'http://localhost:8000/api'
    
    # Test 1: Add test papers
    print("Adding test papers...")
    response = requests.post(f"{base_url}/dev/add-test-papers")
    print(f"Response: {response.status_code}")
    print(response.json())
    
    # Test 2: Get papers
    print("\nGetting papers...")
    response = requests.get(f"{base_url}/papers")
    print(f"Response: {response.status_code}")
    papers = response.json()
    print(f"Found {len(papers)} papers")
    if papers:
        print(f"First paper: {papers[0]['title']}")
    
    # Test 3: Get highlighted papers
    print("\nGetting highlighted papers...")
    response = requests.get(f"{base_url}/papers/highlighted")
    print(f"Response: {response.status_code}")
    highlighted = response.json()
    print(f"Found {len(highlighted)} highlighted papers")
    if highlighted:
        print(f"First highlighted paper: {highlighted[0]['title']}")
    
    # Test 4: Get paper details
    if papers:
        paper_id = papers[0]['uid']
        print(f"\nGetting details for paper {paper_id}...")
        response = requests.get(f"{base_url}/papers/{paper_id}")
        print(f"Response: {response.status_code}")
        details = response.json()
        print(f"Paper details: {details['title']}")

if __name__ == "__main__":
    test_api()