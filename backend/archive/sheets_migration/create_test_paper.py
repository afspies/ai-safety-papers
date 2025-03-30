#!/usr/bin/env python3
"""
Create a test paper in Supabase.
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    sys.exit('Supabase credentials not found in .env file')

try:
    # Initialize Supabase client
    print(f"Connecting to Supabase: {supabase_url}")
    supabase = create_client(supabase_url, supabase_key)
    print("Connected successfully!")
    
    # Create a test paper
    sample_paper = {
        'id': 'test_sample',
        'title': 'Test Sample Paper',
        'authors': ['Test Author'],
        'abstract': 'This is a test abstract',
        'highlight': True,
        'include_on_website': True
    }
    
    try:
        # Try to create the paper
        insert_result = supabase.table("papers").insert(sample_paper).execute()
        print("Sample paper added successfully!")
        print(insert_result)
    except Exception as insert_error:
        print(f"Error adding sample paper: {insert_error}")
        print("\nPlease follow these steps to create the table manually:")
        print("1. Go to the Supabase dashboard")
        print("2. Open the SQL Editor")
        print("3. Paste the following SQL and execute it:")
        
        with open('src/supabase_table_setup.sql', 'r') as f:
            print("\n" + f.read())

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)