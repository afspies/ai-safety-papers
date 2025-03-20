#!/usr/bin/env python3
"""
Script to create tables using the Supabase Python client with stored procedures.
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
    
    # Create papers table
    print("Creating papers table...")
    
    # Use the RPC function to execute DDL commands
    # Note: This function will only work if your Supabase project has this function enabled
    table_result = supabase.table("papers").select("*").limit(1).execute()
    if "error" in table_result or not hasattr(table_result, "data"):
        print("The papers table doesn't exist. Using REST API to create it...")
        
        # Add a sample paper to test the API and create the table through the API
        sample_paper = {
            'id': 'test_sample',
            'title': 'Test Sample Paper',
            'authors': ['Test Author'],
            'abstract': 'This is a test abstract',
            'highlight': True,
            'include_on_website': True
        }
        
        try:
            insert_result = supabase.table("papers").insert(sample_paper).execute()
            print("Sample paper added successfully!")
        except Exception as insert_error:
            print(f"Error adding sample paper: {insert_error}")
            print("\nPlease follow these steps to create the table manually:")
            print("1. Go to the Supabase dashboard")
            print("2. Open the SQL Editor")
            print("3. Paste the following SQL and execute it:")
            
            with open('src/supabase_table_setup.sql', 'r') as f:
                print("\n" + f.read())
    else:
        print("Papers table exists!")
        
        # Test the table by adding a sample paper
        sample_paper = {
            'id': 'test_sample',
            'title': 'Test Sample Paper',
            'authors': ['Test Author'],
            'abstract': 'This is a test abstract',
            'highlight': True,
            'include_on_website': True
        }
        
        try:
            insert_result = supabase.table("papers").insert(sample_paper).execute()
            print("Sample paper added successfully!")
        except Exception as insert_error:
            print(f"Error adding sample paper: {insert_error}")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)