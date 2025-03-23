#!/usr/bin/env python3
import requests
import json

def run_pipeline_and_check_api():
    # First add the real paper from Semantic Scholar
    print("Running pipeline to add a real paper...")
    import subprocess
    import sys
    import os
    
    # Run the pipeline script
    env = os.environ.copy()
    env['DEVELOPMENT_MODE'] = 'true'
    env['PYTHONPATH'] = '/Users/alex/Desktop/playground/ai-safety-papers'
    
    subprocess.run(
        [sys.executable, 'backend/run_processing.py'],
        env=env,
        check=True
    )
    
    # Now check the API to see if the paper is there
    print("\nChecking API for papers...")
    base_url = 'http://localhost:8000/api'
    response = requests.get(f"{base_url}/papers")
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
        
    papers = response.json()
    print(f"Found {len(papers)} papers")
    
    # Look for a paper that's not one of our sample papers
    real_paper = None
    for paper in papers:
        if paper['uid'] != 'sample-paper-1' and paper['uid'] != 'sample-paper-2':
            real_paper = paper
            break
    
    if real_paper:
        print("\nFound real paper from Semantic Scholar:")
        print(f"Title: {real_paper['title']}")
        print(f"ID: {real_paper['uid']}")
        print(f"Authors: {', '.join(real_paper['authors'])}")
        print(f"TLDR: {real_paper['tldr']}")
        
        # Get the paper details
        print("\nGetting paper details...")
        response = requests.get(f"{base_url}/papers/{real_paper['uid']}")
        if response.status_code == 200:
            details = response.json()
            print("Paper details retrieved successfully")
            print(f"Summary: {details['summary'][:100]}...")
        else:
            print(f"Error getting paper details: {response.status_code}")
    else:
        print("\nNo real paper from Semantic Scholar found in the API")

if __name__ == "__main__":
    run_pipeline_and_check_api()