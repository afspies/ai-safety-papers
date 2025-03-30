#!/usr/bin/env python3
"""
Test inserting a paper into Supabase.
Assumes the papers table has been manually created in the Supabase SQL Editor.
"""
import os
import sys
from datetime import datetime
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
        'id': 'test_sample_1',
        'title': 'Test Sample Paper',
        'authors': ['Test Author 1', 'Test Author 2'],
        'year': '2025',
        'abstract': 'This is a test abstract for Supabase integration.',
        'url': 'https://example.com/paper1',
        'venue': 'AI Safety Conference',
        'tldr': 'Sample TLDR for testing',
        'submitted_date': datetime.now().isoformat(),
        'highlight': True,
        'include_on_website': True,
        'post_to_bots': False,
        'ai_safety_relevance': 5,
        'mech_int_relevance': 3,
        'embedding_model': 'test-model',
        'embedding_vector': [0.1, 0.2, 0.3, 0.4],
        'tags': ['ai safety', 'testing']
    }
    
    # Try to insert the paper
    print("Inserting test paper...")
    result = supabase.table('papers').insert(sample_paper).execute()
    
    if result.data:
        print(f"Successfully inserted paper with ID: {result.data[0]['id']}")
        
        # Now try to retrieve it
        print("\nRetrieving the paper...")
        get_result = supabase.table('papers').select('*').eq('id', 'test_sample_1').execute()
        
        if get_result.data:
            print(f"Successfully retrieved paper: {get_result.data[0]['title']}")
        else:
            print("Failed to retrieve paper")
    else:
        print(f"Failed to insert paper: {result}")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)