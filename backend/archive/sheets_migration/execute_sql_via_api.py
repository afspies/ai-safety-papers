#!/usr/bin/env python3
"""
Script to execute SQL directly via Supabase's REST API.
"""
import os
import sys
import base64
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    sys.exit('Supabase credentials not found in .env file')

try:
    # Create Management API URL (note: this requires service_role key, not anon key)
    management_url = f"{supabase_url}/rest/v1/"
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    # First, check if the table exists
    print("Checking if papers table exists...")
    try:
        # Try to access the papers table
        response = requests.get(f"{management_url}papers?limit=1", headers=headers)
        
        if response.status_code == 200:
            print("Table exists!")
        else:
            print(f"Table doesn't exist (status code {response.status_code})")
            # Try to create the table directly with a sample paper
            sample_paper = {
                'id': 'test_sample',
                'title': 'Test Sample Paper',
                'authors': ['Test Author'],
                'abstract': 'This is a test abstract',
                'highlight': True,
                'include_on_website': True
            }
            
            # Attempt to insert a sample paper (this will fail but gives useful error info)
            insert_response = requests.post(f"{management_url}papers", headers=headers, json=sample_paper)
            print(f"Insert attempt result: {insert_response.status_code} - {insert_response.text}")
            
            # Print instructions for manual creation
            print("\nYou need to create the table manually in the Supabase SQL Editor.")
            print("1. Log in to the Supabase dashboard")
            print("2. Go to the SQL Editor")
            print("3. Paste the following SQL and execute it:")
            
            with open('src/supabase_table_setup.sql', 'r') as f:
                print("\n" + f.read())
            
    except Exception as e:
        print(f"Error checking table: {e}")
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)