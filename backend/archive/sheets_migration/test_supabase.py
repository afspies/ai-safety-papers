#!/usr/bin/env python3
"""
Test script for Supabase integration.
"""
import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from models.supabase import SupabaseDB

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_sample_papers():
    """Create sample paper data for testing."""
    return [
        {
            'id': 'sample1',
            'title': 'Sample AI Safety Paper 1',
            'authors': ['Author One', 'Author Two'],
            'year': '2025',
            'abstract': 'This is a sample abstract for testing Supabase integration.',
            'url': 'https://example.com/paper1',
            'venue': 'AI Safety Conference',
            'tldr': 'Sample TLDR for the first paper',
            'submitted_date': datetime.now().isoformat(),
            'highlight': True,
            'include_on_website': True,
            'post_to_bots': True,
            'ai_safety_relevance': 5,
            'mech_int_relevance': 3,
            'embedding_model': 'test-model',
            'embedding_vector': [0.1, 0.2, 0.3, 0.4],
            'tags': ['ai safety', 'testing']
        },
        {
            'id': 'sample2',
            'title': 'Sample AI Safety Paper 2',
            'authors': ['Author Three', 'Author Four'],
            'year': '2025',
            'abstract': 'This is another sample abstract for testing Supabase integration.',
            'url': 'https://example.com/paper2',
            'venue': 'AI Safety Workshop',
            'tldr': 'Sample TLDR for the second paper',
            'submitted_date': datetime.now().isoformat(),
            'highlight': False,
            'include_on_website': True,
            'post_to_bots': False,
            'ai_safety_relevance': 4,
            'mech_int_relevance': 2,
            'embedding_model': 'test-model',
            'embedding_vector': [0.5, 0.6, 0.7, 0.8],
            'tags': ['ai safety', 'alignment']
        }
    ]

def test_supabase_connection():
    """Test that we can connect to Supabase."""
    try:
        load_dotenv()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found in .env file")
            return False
        
        # Initialize Supabase client
        db = SupabaseDB(supabase_url, supabase_key)
        logger.info("Successfully connected to Supabase")
        return True
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {e}")
        return False

def test_add_papers():
    """Test adding papers to Supabase."""
    try:
        load_dotenv()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found in .env file")
            return False
        
        # Initialize Supabase client
        db = SupabaseDB(supabase_url, supabase_key)
        
        # Create sample papers
        papers = create_sample_papers()
        
        # Add papers to Supabase
        for paper in papers:
            result = db.add_paper(paper)
            logger.info(f"Added paper: {result['id']}")
        
        logger.info("Successfully added papers to Supabase")
        return True
    except Exception as e:
        logger.error(f"Error adding papers to Supabase: {e}")
        return False

def test_get_papers():
    """Test getting papers from Supabase."""
    try:
        load_dotenv()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found in .env file")
            return False
        
        # Initialize Supabase client
        db = SupabaseDB(supabase_url, supabase_key)
        
        # Get all papers (may return Article objects, not raw dictionaries)
        papers = db.get_papers()
        logger.info(f"Retrieved {len(papers)} papers from Supabase")
        
        # Get highlighted papers
        highlighted = db.get_highlighted_papers()
        logger.info(f"Retrieved {len(highlighted)} highlighted papers from Supabase")
        
        # Get paper by ID
        paper = db.get_paper_by_id('sample1')
        if paper:
            logger.info(f"Retrieved paper by ID: {paper['id']}")
        else:
            logger.warning("Could not retrieve paper by ID")
        
        return True
    except Exception as e:
        logger.error(f"Error getting papers from Supabase: {e}")
        return False

def main():
    """Main function to run tests."""
    logger.info("Testing Supabase integration")
    
    if not test_supabase_connection():
        logger.error("Failed to connect to Supabase")
        return
    
    if not test_add_papers():
        logger.error("Failed to add papers to Supabase")
        return
    
    if not test_get_papers():
        logger.error("Failed to get papers from Supabase")
        return
    
    logger.info("All tests completed successfully")

if __name__ == "__main__":
    main()