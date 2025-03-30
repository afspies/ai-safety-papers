import sys
import os
import time
import logging
from backend.src.utils.config_loader import load_config
from backend.src.api.semantic_scholar import SemanticScholarAPI
from backend.src.models.supabase import SupabaseDB
from datetime import datetime
import argparse
from backend.src.summarizer.paper_summarizer import PaperSummarizer
from backend.src.models.article import Article
import shutil
from pathlib import Path
import re
import json
from backend.src.markdown.post_generator import create_post_markdown

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up logging
DEBUG_MODE = True  # Set this to False to disable debug logs

# Initialize logger at the top of the file
logger = logging.getLogger(__name__)

def setup_logging():
    log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Filter out noisy loggers
    logging.getLogger('pdfminer').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore.http11').setLevel(logging.WARNING)
    logging.getLogger('papermage').setLevel(logging.WARNING)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    logging.getLogger('anthropic._base_client').setLevel(logging.WARNING)
    logging.getLogger('PIL.PngImagePlugin').setLevel(logging.WARNING)

def main():
    setup_logging()
    logger.info("Starting AI-Safety Reading List application")
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="AI-Safety Reading List application")
    parser.add_argument("--ignore-date-range", action="store_true", help="Ignore date range when fetching papers")
    parser.add_argument("--months", type=int, default=1, help="Number of months to look back for papers (default: 1)")
    parser.add_argument("--reprocess", choices=['figures', 'summary', 'markdown', 'info', 'all'], 
                       help="Reprocess specific parts of existing papers: figures, summary, markdown, info (re-query API), or all")
    parser.add_argument("--paper-id", help="Specific paper ID to reprocess (optional)")
    parser.add_argument("--api", action="store_true", help="Run as API server instead of processing pipeline")
    args = parser.parse_args()
    
    try:
        config = load_config()
        logger.debug("Configuration loaded successfully")
        
        # If API mode is requested, start the FastAPI server
        if args.api:
            logger.info("Starting in API server mode")
            # Set environment variable for API mode
            os.environ['API_MODE'] = 'true'
            
            # Check for development mode to bypass API key checks
            if os.environ.get('DEVELOPMENT_MODE') == 'true':
                logger.info("Running in development mode - bypassing API key checks")
                # Directly start the FastAPI server without initializing API clients
                from backend.src.api.server import start
                start()
                return
            else:
                from backend.src.api.server import start
                start()
                return
        
        # Check if we're in development mode
        if os.environ.get('DEVELOPMENT_MODE') == 'true':
            logger.info("Running in development mode - using mock API clients")
            # Use development/mock API client
            semantic_scholar_api = SemanticScholarAPI(config['semantic_scholar']['api_key'], development_mode=True)
            logger.debug("Mock Semantic Scholar API initialized for development")
            
            # Use mock database client
            from backend.src.api.routers import MockSupabaseDB
            db = MockSupabaseDB()
            logger.debug("Mock Supabase DB initialized for development")
        else:
            # Production mode - initialize with or without API key
            api_key = config.get('semantic_scholar', {}).get('api_key')
            
            # API key is now optional for Semantic Scholar
            semantic_scholar_api = SemanticScholarAPI(api_key)
            logger.debug("Semantic Scholar API initialized")
            
            # Supabase still requires credentials
            if not config.get('supabase', {}).get('url') or not config.get('supabase', {}).get('key'):
                logger.warning("Supabase credentials not found. Using mock database.")
                from backend.src.api.routers import MockSupabaseDB
                db = MockSupabaseDB()
                logger.debug("Mock Supabase DB initialized due to missing credentials")
            else:
                db = SupabaseDB()
                logger.debug("Supabase DB initialized")

        while True:
            logger.info("Starting new processing cycle")
            # Fetch and process new papers
            process_new_papers(semantic_scholar_api, db, ignore_date_range=args.ignore_date_range, months=args.months)

            # Check for manually flagged papers
            process_flagged_papers(db, args)

            logger.info("Processing cycle completed. Waiting for next cycle.")
            # Wait for the next cycle (e.g., every 24 hours)
            time.sleep(24 * 60 * 60)
    except Exception as e:
        logger.error(f"An error occurred during initialization: {e}")
        sys.exit(1)

def process_new_papers(api: SemanticScholarAPI, db: SupabaseDB, ignore_date_range: bool = False, months: int = 1):
    logger.info(f"Processing new papers (ignore_date_range: {ignore_date_range}, months: {months})")
    
    # Get existing paper IDs from the database first
    existing_papers = set()
    try:
        # For Supabase, get all papers and extract IDs
        papers = db.get_papers()
        existing_papers = {paper.uid for paper in papers}
        logger.debug(f"Found {len(existing_papers)} existing papers in database")
    except Exception as e:
        logger.error(f"Error loading existing papers: {e}")
        return
    
    # Add tracking of processed papers to avoid duplicates within the same run
    processed_paper_ids = set()
    
    queries = ["AI Safety", "Mechanistic Interpretability"]
    
    all_papers = []
    for query in queries:
        try:
            logger.debug(f"Fetching papers for query: {query}")
            papers = api.get_relevant_papers(query, months=months, limit=100, ignore_date_range=ignore_date_range)
            
            # Filter out papers that exist in DB or were already processed in this run
            new_papers = [p for p in papers 
                         if p['paperId'] not in existing_papers 
                         and p['paperId'] not in processed_paper_ids]
            
            logger.debug(f"Found {len(new_papers)} new papers for query: {query} "
                        f"(filtered from {len(papers)} total)")
            
            all_papers.extend(new_papers)
            # Add these paper IDs to our processed set
            processed_paper_ids.update(p['paperId'] for p in new_papers)
            
        except Exception as e:
            logger.error(f"Failed to search for papers with query '{query}': {e}")
            logger.exception("Full traceback:")
    
    if not all_papers:
        logger.info("No new papers found")
        return

    for paper in all_papers:
        logger.debug(f"Processing paper: {paper['paperId']}")
        try:
            # Verify paper ID exists and is valid
            if not paper.get('paperId'):
                logger.warning("Skipping paper with missing ID")
                continue
                
            # Create entry with the correct ID field
            entry = {
                'id': paper['paperId'],
                'title': paper.get('title', ''),
                'authors': [author.get('name', '') for author in paper.get('authors', [])],
                'year': paper.get('year'),
                'abstract': paper.get('abstract', ''),
                'url': paper.get('url', ''),
                'venue': paper.get('venue', ''),
                'submitted_date': datetime.fromisoformat(paper.get('publicationDate', '').split('T')[0]) 
                                if paper.get('publicationDate') else None,
                'query': paper.get('query', ''),
                'tldr': paper.get('tldr', {}),
                'embedding': paper.get('embedding', {})
            }
            
            # Add entry to database
            db.add_paper(entry)
            logger.debug(f"Successfully processed paper: {paper['paperId']}")
            
        except Exception as e:
            logger.error(f"Failed to process paper {paper.get('paperId', 'unknown')}: {e}")
            logger.exception("Full traceback:")
            continue
    
    logger.debug(f"Processed {len(all_papers)} new papers in total")

def process_flagged_papers(db: SupabaseDB, args):
    logger.info("Starting process_flagged_papers")
    
    try:
        logger.debug("Loading config...")
        config = load_config()
        
        # Initialize API if needed for reprocessing info
        semantic_scholar_api = None
        if args.reprocess in ['info', 'all']:
            # Check if we're in development mode
            if os.environ.get('DEVELOPMENT_MODE') == 'true':
                semantic_scholar_api = SemanticScholarAPI(config['semantic_scholar']['api_key'], development_mode=True)
                logger.debug("Initialized mock Semantic Scholar API for development")
            else:
                api_key = config['semantic_scholar']['api_key']
                semantic_scholar_api = SemanticScholarAPI(api_key)
                logger.debug("Initialized Semantic Scholar API for reprocessing")
        
        # Get papers based on command line args
        if args.paper_id:
            paper_obj = db.get_paper_by_id(args.paper_id)
            if not paper_obj:
                logger.error(f"Paper with ID {args.paper_id} not found")
                return
            papers_to_post = [paper_obj]
        else:
            # Get all papers to post but limit to 10 for testing
            papers_to_post = db.get_papers_to_post()[:10]
            logger.info(f"Limiting to 10 papers for testing")
            
        logger.debug(f"Found {len(papers_to_post)} papers to process")
        
        logger.debug("Setting up website content path...")
        website_content_path = Path(config.get('website', {}).get('content_path', '../ai-safety-site/content/en'))
        logger.debug(f"Using website content path: {website_content_path}")
        
        posts_path = website_content_path / "posts"
        logger.debug(f"Creating posts directory at: {posts_path}")
        posts_path.mkdir(parents=True, exist_ok=True)
        
        logger.debug("Initializing PaperSummarizer...")
        # In development mode, use a mock summarizer
        if os.environ.get('DEVELOPMENT_MODE') == 'true':
            summarizer = PaperSummarizer(config['anthropic']['api_key'], development_mode=True)
            logger.debug("Mock PaperSummarizer initialized for development")
        else:
            summarizer = PaperSummarizer(config['anthropic']['api_key'])
            logger.debug("PaperSummarizer initialized successfully")
        
        for i, paper in enumerate(papers_to_post):
            paper_id = paper.uid if hasattr(paper, 'uid') else getattr(paper, 'id', 'unknown id')
            logger.info(f"Processing paper {i+1}/{len(papers_to_post)}: {paper_id}")
            try:
                # Reprocess paper info if requested
                if args.reprocess in ['info', 'all']:
                    try:
                        logger.debug(f"Re-querying API for paper {paper_id}")
                        updated_info = semantic_scholar_api.fetch_paper_details_batch([paper_id])[0]
                        if updated_info:
                            # Create paper data dictionary for updating
                            paper_data = {
                                'id': paper_id,
                                'title': updated_info.get('title', paper.title if hasattr(paper, 'title') else ''),
                                'authors': [a.get('name', '') for a in updated_info.get('authors', [])],
                                'year': updated_info.get('year'),
                                'abstract': updated_info.get('abstract', paper.abstract if hasattr(paper, 'abstract') else ''),
                                'url': updated_info.get('url', paper.url if hasattr(paper, 'url') else ''),
                                'venue': updated_info.get('venue', paper.venue if hasattr(paper, 'venue') else ''),
                                'tldr': updated_info.get('tldr', paper.tldr if hasattr(paper, 'tldr') else ''),
                            }
                            # Update the database entry
                            db.update_paper(paper_data)
                            logger.info(f"Updated paper info for {paper_id}")
                    except Exception as e:
                        logger.error(f"Failed to update paper info for {paper_id}: {e}")
                
                # We may already have an Article instance
                if isinstance(paper, Article):
                    article = paper
                else:
                    # Create article instance from dictionary or data object
                    article = create_article_instance(paper)
                
                # Set up data paths
                paper_dir = Path(config['data_dir']) / article.uid
                pdf_path = paper_dir / "paper.pdf"
                article.set_data_paths(paper_dir, pdf_path)
                
                # Only download PDF if needed
                if not pdf_path.exists() or args.reprocess == 'all':
                    if not article.download_pdf():
                        logger.error(f"Skipping paper {article.uid} due to PDF download failure")
                        continue
                
                # Process figures if requested or needed
                if args.reprocess in ['figures', 'all'] or not (paper_dir / "figures").exists():
                    if not article.process_figures():
                        logger.error(f"Skipping paper {article.uid} due to figure processing failure")
                        continue
                
                # Generate summary if requested or needed
                summary_path = paper_dir / "summary.json"
                if args.reprocess in ['summary', 'all'] or not summary_path.exists():
                    logger.debug("Generating summary...")
                    summary, display_figures, thumbnail_figure = summarizer.summarize(article)
                else:
                    # Load existing summary
                    with open(summary_path, 'r', encoding='utf-8') as f:
                        summary_data = json.load(f)
                    summary = summary_data['summary']
                    display_figures = summary_data['display_figures']
                    thumbnail_figure = summary_data.get('thumbnail_figure')
                
                # Convert display_figures and set article properties
                internal_display_figures = [f"fig_0_{num}" for num in display_figures]
                article.set_displayed_figures(internal_display_figures)
                
                # Set thumbnail source
                if thumbnail_figure and str(thumbnail_figure).isdigit():
                    for fig_id in article.figures:
                        if fig_id.startswith(f"fig_0_{thumbnail_figure}_"):
                            label_match = re.search(r'_(fig\d+|tab\d+|unk)$', fig_id)
                            if label_match:
                                article.set_thumbnail_source(label_match.group(1))
                                break
                    else:
                        logger.warning(f"No matching figure found for thumbnail {thumbnail_figure}, using 'full' mode")
                        article.set_thumbnail_source('full')
                else:
                    article.set_thumbnail_source('full')
                
                # Create website post if requested or needed
                post_dir = posts_path / f"paper_{article.uid}"
                if args.reprocess in ['markdown', 'all'] or not post_dir.exists():
                    create_website_post(article, summary, posts_path)
                
                # Only mark as posted if this is a new paper
                if not args.reprocess:
                    db.mark_as_posted(article.uid)
                    
                logger.info(f"Successfully processed paper: {article.uid}")
                
            except Exception as e:
                logger.error(f"Error processing paper {paper_id}: {e}")
                logger.exception("Full traceback:")
                continue
                
    except Exception as e:
        logger.error(f"Error during flagged papers processing: {str(e)}")
        logger.error(f"Config keys available: {list(config.keys()) if 'config' in locals() else 'No config loaded'}")
        logger.exception("Full traceback:")
    
    logger.info("Finished process_flagged_papers")

def create_article_instance(paper: dict) -> Article:
    """Create and initialize an Article instance from paper data."""
    article = Article(paper['id'], paper['title'], paper['url'])
    article.set_authors(paper.get('authors', []))
    if 'abstract' in paper:
        article.set_abstract(paper['abstract'])
    
    # Add TLDR if available - handle both API and database formats
    if 'tldr' in paper:
        if isinstance(paper['tldr'], dict):
            tldr_text = paper['tldr'].get('text')
        else:
            tldr_text = paper['tldr']  # Direct string from database
        if tldr_text:
            article.set_tldr(tldr_text)
            logger.debug(f"Set TLDR for article {article.uid}: {tldr_text[:100]}...")
    
    # Set highlight status
    if 'highlight' in paper:
        article.highlight = paper['highlight']
        logger.debug(f"Set highlight status for article {article.uid}: {article.highlight}")
    
    return article

def create_website_post(article: Article, summary: str, posts_path: Path):
    """Create a new post in the website's content directory."""
    logger = logging.getLogger(__name__)
    
    # Create post directory
    post_dir = posts_path / f"paper_{article.uid}"
    logger.debug(f"Creating post directory at: {post_dir}")
    post_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy thumbnail and handle figures
    thumbnail = article.create_thumbnail()
    if thumbnail and thumbnail.exists():
        logger.debug(f"Copying thumbnail to post directory: {thumbnail}")
        shutil.copy2(thumbnail, post_dir / "thumbnail.png")
    else:
        logger.warning(f"No thumbnail found for article {article.uid}")
    
    # Create a Post object for markdown generation
    from backend.src.models.post import Post
    post = Post(article, summary, post_dir)
    
    # Process figures for the post
    figures = {}
    for fig_id, fig_path in article.figures.items():
        from backend.src.models.figure import Figure
        figure = Figure(fig_id)
        figure.load_from_path(fig_path)
        figures[fig_id] = figure
    
    post.figures = figures
    
    # Create markdown post with updated figure references
    post_content = create_post_markdown(post)
    markdown_path = post_dir / "index.md"
    logger.debug(f"Writing markdown content to {markdown_path}")
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(post_content)
    
    logger.debug(f"Created website post for paper {article.uid}")

def clean_latex(text: str) -> str:
    """Clean and convert LaTeX to proper format for Hugo/KaTeX."""
    if not text:
        return text
        
    # Fix common LaTeX formatting issues
    text = re.sub(r'\\bm\{([^}]+)\}', r'\\mathbf{\1}', text)  # Convert \bm to \mathbf
    text = re.sub(r'\\1m\{([^}]+)\}', r'\\mathbf{\1}', text)  # Fix ar5iv-specific formatting
    
    # Fix subscript and superscript formatting
    text = re.sub(r'subscript([^}]+)}', r'_{\1}', text)
    text = re.sub(r'superscript([^}]+)}', r'^{\1}', text)
    
    # Fix operator formatting
    text = re.sub(r'\\operatorname\*?\{([^}]+)\}', r'\\operatorname{\1}', text)
    
    # Ensure proper spacing around math delimiters
    text = re.sub(r'([^$])\$([^$])', r'\1 $\2', text)  # Add space around inline math
    text = re.sub(r'\$\$', r' $$ ', text)  # Add space around display math
    
    # Remove any duplicate spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text

def escape_yaml(text: str) -> str:
    """Escape text for YAML frontmatter."""
    if not text:
        return ""
    
    # Only escape quotes and backslashes
    text = text.replace('\\', '\\\\')  # escape backslashes first
    text = text.replace('"', '\\"')    # escape quotes
    
    # Remove any accidental double escapes
    text = text.replace('\\\\\\', '\\\\')
    
    return text

if __name__ == "__main__":
    main()
