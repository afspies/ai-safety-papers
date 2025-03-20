#!/usr/bin/env python3
"""
Script to run the full AI Safety Papers processing pipeline with a real-world paper.
This script uses the Semantic Scholar API directly to get a paper
and processes it through our pipeline.
"""

import os
import sys
from pathlib import Path
import logging
import json
import requests

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from backend.src.utils.config_loader import load_config
from backend.src.api.semantic_scholar import SemanticScholarAPI
from backend.src.models.article import Article
# Create our own MockSupabaseDB without importing from routers
class MockSupabaseDB:
    def __init__(self):
        logger.info("Initializing mock SupabaseDB for standalone script")
        self.papers = []  # In-memory storage for development
        self.highlighted_papers = []  # In-memory storage for highlighted papers
        
    def get_papers(self):
        # Return stored papers as Article objects
        articles = []
        for paper in self.papers:
            article = Article(
                uid=paper.get('id', ''),
                title=paper.get('title', ''),
                url=paper.get('url', '')
            )
            article.set_authors(paper.get('authors', []))
            article.set_abstract(paper.get('abstract', ''))
            if paper.get('tldr'):
                article.set_tldr(paper.get('tldr', ''))
            articles.append(article)
        return articles
        
    def get_highlighted_papers(self):
        # Return highlighted papers
        return self.highlighted_papers
        
    def get_paper_by_id(self, paper_id):
        # Find paper by ID
        for paper in self.papers:
            if paper.get('id') == paper_id:
                return paper
        return None
        
    def add_paper(self, paper_data):
        # Add paper to in-memory storage
        self.papers.append(paper_data)
        logger.info(f"Added paper to mock DB: {paper_data.get('id')}")
        return True
from backend.src.summarizer.paper_summarizer import PaperSummarizer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Load configuration
    config = load_config()
    logger.info("Configuration loaded")
    
    # Create API clients for real data
    # Set development_mode=False for real data, True for mock data
    semantic_scholar_api = SemanticScholarAPI(api_key=None, development_mode=False)
    logger.info("Semantic Scholar API initialized")
    
    # Use mock database for simplicity
    db = MockSupabaseDB()
    logger.info("Mock Supabase DB initialized")
    
    # Get one real paper from Semantic Scholar
    logger.info("Fetching a real paper from Semantic Scholar...")
    papers = semantic_scholar_api.get_relevant_papers(
        query="AI Safety", 
        months=3,  # Increase to 3 months to find more papers
        limit=10,   # Increase limit to find at least one paper
        ignore_date_range=True  # Ignore date range to get more results
    )
    
    if not papers:
        logger.error("No papers found from Semantic Scholar API")
        return
    
    # Get the paper data
    paper = papers[0]
    logger.info(f"Found paper: {paper['title']} (ID: {paper['paperId']})")
    
    # Process the paper
    try:
        # Add paper to database
        entry = {
            'id': paper['paperId'],
            'title': paper.get('title', ''),
            'authors': [author.get('name', '') for author in paper.get('authors', [])],
            'year': paper.get('year'),
            'abstract': paper.get('abstract', ''),
            'url': paper.get('url', ''),
            'venue': paper.get('venue', ''),
            'submitted_date': paper.get('publicationDate', '').split('T')[0] if paper.get('publicationDate') else None,
            'query': paper.get('query', ''),
            'tldr': paper.get('tldr', {}).get('text', '') if isinstance(paper.get('tldr'), dict) else paper.get('tldr', '')
        }
        
        db.add_paper(entry)
        logger.info(f"Added paper to database: {paper['paperId']}")
        
        # Print the paper data
        logger.info(f"Paper details: {json.dumps(entry, indent=2)}")
        
        # Check the API to see if the paper was added
        logger.info("Verifying paper was added to mock database...")
        papers = db.get_papers()
        logger.info(f"Database now contains {len(papers)} papers")
        
        # Print the database content
        for p in papers:
            logger.info(f"DB Paper: {p.title} (ID: {p.uid})")
        
    except Exception as e:
        logger.error(f"Error processing paper: {e}")
    
if __name__ == "__main__":
    main()