#!/usr/bin/env python3
import requests
import json

def check_papers():
    # Base URL
    base_url = 'http://localhost:8000/api'
    
    # Get all papers
    print("Getting all papers...")
    response = requests.get(f"{base_url}/papers")
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
        
    papers = response.json()
    print(f"Found {len(papers)} papers:")
    
    for i, paper in enumerate(papers):
        print(f"{i+1}. {paper['title']} (ID: {paper['uid']})")
        print(f"   Authors: {', '.join(paper['authors'])}")
        print(f"   TLDR: {paper['tldr']}")
        print(f"   Highlight: {paper['highlight']}")
        print()

if __name__ == "__main__":
    check_papers()