#!/usr/bin/env python3
"""
Check if the papers table exists in Supabase.
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

# Check if the table exists
api_url = f"{supabase_url}/rest/v1/papers?limit=1"

headers = {
    'apikey': supabase_key,
    'Authorization': f'Bearer {supabase_key}'
}

try:
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Table exists and is accessible via the API!")
        
        # Try to add a sample paper
        sample_url = f"{supabase_url}/rest/v1/papers"
        sample_paper = {
            'id': 'api_test_sample',
            'title': 'API Test Sample Paper',
            'authors': ['Test Author'],
            'abstract': 'This is a test abstract from the API test',
            'highlight': True,
            'include_on_website': True
        }
        
        insert_headers = headers.copy()
        insert_headers['Content-Type'] = 'application/json'
        insert_headers['Prefer'] = 'return=representation'
        
        insert_response = requests.post(sample_url, headers=insert_headers, json=sample_paper)
        
        if insert_response.status_code in [200, 201]:
            print("✅ Successfully inserted test paper via API!")
            print(f"Paper data: {insert_response.json()}")
            print("\nThe Supabase table is set up correctly and ready to use.")
        else:
            print(f"❌ Failed to insert test paper via API: {insert_response.status_code}")
            print(f"Error: {insert_response.text}")
    else:
        print(f"❌ Table doesn't exist or isn't accessible: {response.status_code}")
        print(f"Error: {response.text}")
        print("\nYou need to create the table in the Supabase SQL Editor.")
        
except Exception as e:
    print(f"❌ Error checking table: {e}")
    sys.exit(1)