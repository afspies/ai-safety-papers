#!/usr/bin/env python3
"""
Script to create tables in Supabase using the REST API.
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    sys.exit('Supabase credentials not found in .env file')

# Create REST API URL
api_url = f'{supabase_url}/rest/v1/papers'

# Set headers for authentication
headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

# Add sample papers to test the connection
try:
    # First try to check if the table exists
    print("Checking if papers table exists...")
    check_response = requests.get(f'{supabase_url}/rest/v1/papers?limit=1', headers=headers)
    
    if check_response.status_code != 200:
        print(f"Table doesn't exist or error occurred: {check_response.status_code}")
        print("You need to create the table manually in the Supabase SQL Editor with this SQL:")
        
        with open('src/supabase_table_setup.sql', 'r') as f:
            print("\n" + f.read())
    else:
        print("Table exists!")
        
        # Add a sample paper
        sample_paper = {
            'id': 'sample_test',
            'title': 'Sample Paper for Testing',
            'authors': ['Test Author'],
            'abstract': 'This is a test abstract',
            'url': 'https://example.com/test',
            'highlight': True,
            'include_on_website': True
        }
        
        print("Adding sample paper...")
        response = requests.post(api_url, headers=headers, json=sample_paper)
        
        if response.status_code in [200, 201, 204]:
            print("Sample paper added successfully!")
        else:
            print(f"Error adding sample paper: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)