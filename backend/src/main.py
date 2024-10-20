import sys
import os
import time
import logging
from utils.config_loader import load_config
from api.semantic_scholar import SemanticScholarAPI
from sheets.sheets_db import SheetsDB
from datetime import datetime
import argparse

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up logging
DEBUG_MODE = True  # Set this to False to disable debug logs

def setup_logging():
    log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting AI-Safety Reading List application")
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="AI-Safety Reading List application")
    parser.add_argument("--ignore-date-range", action="store_true", help="Ignore date range when fetching papers")
    parser.add_argument("--months", type=int, default=1, help="Number of months to look back for papers (default: 1)")
    args = parser.parse_args()
    
    try:
        config = load_config()
        logger.debug("Configuration loaded successfully")
        
        api_key = config['semantic_scholar']['api_key']
        if not api_key or api_key == "your_semantic_scholar_api_key_here":
            raise ValueError("Semantic Scholar API key is not set in the config file")
        
        semantic_scholar_api = SemanticScholarAPI(api_key)
        logger.debug("Semantic Scholar API initialized")
        
        sheets_db = SheetsDB(
            config['google_sheets']['spreadsheet_id'],
            config['google_sheets']['range_name'],
            config['google_sheets']['credentials_file']
        )
        logger.debug("Google Sheets DB initialized")

        while True:
            logger.info("Starting new processing cycle")
            # Fetch and process new papers
            process_new_papers(semantic_scholar_api, sheets_db, ignore_date_range=args.ignore_date_range, months=args.months)

            # Check for manually flagged papers
            process_flagged_papers(sheets_db)

            logger.info("Processing cycle completed. Waiting for next cycle.")
            # Wait for the next cycle (e.g., every 24 hours)
            time.sleep(24 * 60 * 60)
    except Exception as e:
        logger.error(f"An error occurred during initialization: {e}")
        sys.exit(1)

def process_new_papers(api: SemanticScholarAPI, db: SheetsDB, ignore_date_range: bool = False, months: int = 1):
    logger = logging.getLogger(__name__)
    logger.info(f"Processing new papers (ignore_date_range: {ignore_date_range}, months: {months})")
    
    queries = ["AI Safety", "Mechanistic Interpretability"]
    
    all_papers = []
    for query in queries:
        try:
            papers = api.get_relevant_papers(query, months=months, limit=100, ignore_date_range=ignore_date_range)
            all_papers.extend(papers)
            logger.info(f"Found {len(papers)} papers for query: {query}")
        except Exception as e:
            logger.error(f"Failed to search for papers with query '{query}': {e}")
    
    if not all_papers:
        logger.warning("No papers found or error occurred while fetching papers")
        return

    for paper in all_papers:
        logger.debug(f"Processing paper: {paper['paperId']}")
        try:
            submitted_date = datetime.fromisoformat(paper.get('publicationDate', '').split('T')[0]) if paper.get('publicationDate') else None
            db.add_entry({
                'id': paper['paperId'],
                'title': paper['title'],
                'authors': [author['name'] for author in paper.get('authors', [])],
                'year': paper.get('year'),
                'abstract': paper.get('abstract', ''),
                'url': paper.get('url', ''),
                'venue': paper.get('venue', ''),
                'submitted_date': submitted_date,
                'query': paper['query'],
                'tldr': paper.get('tldr', {}),
                'embedding': paper.get('embedding', {})
            })
        except Exception as e:
            logger.error(f"Failed to add paper {paper['paperId']} to database: {e}")
    
    logger.debug(f"Processed {len(all_papers)} new papers in total")

def process_flagged_papers(db: SheetsDB):
    logger = logging.getLogger(__name__)
    logger.info("Processing flagged papers")
    papers_to_post = db.get_papers_to_post()
    logger.debug(f"Found {len(papers_to_post)} papers to post")
    for paper in papers_to_post:
        # Implement logic to post papers to bots
        logger.debug(f"Posting paper: {paper['id']}")
        # After posting, mark the paper as posted
        db.mark_as_posted(paper['id'])
    logger.info("Finished processing flagged papers")

if __name__ == "__main__":
    main()
