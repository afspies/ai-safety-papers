#!/usr/bin/env python3
"""
Script to run the AI Safety Papers processing pipeline.
This script separates the pipeline into fetching and processing functions,
allowing for more flexibility in running each stage independently.
"""

import os
import sys
from pathlib import Path
import logging
import argparse
import json
import requests
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import project modules
from src.utils.config_loader import load_config
from src.api.semantic_scholar import SemanticScholarAPI
from src.models.article import Article
from src.models.post import Post
from src.models.figure import Figure
from src.models.supabase import SupabaseDB
from src.summarizer.paper_summarizer import PaperSummarizer
from src.figure_extraction import FigureExtractorManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

WEBSITE_CONTENT_PATH = "processed_papers"

def fetch_papers(paper_id=None, query="AI Safety", months=3, limit=10, 
                ignore_date_range=False, mark_for_site=False, db=None):
    """
    Fetch papers from Semantic Scholar and store them in the database.
    
    Args:
        paper_id: Specific paper ID to fetch (optional)
        query: Search query for Semantic Scholar
        months: Number of months to look back
        limit: Maximum number of papers to fetch
        ignore_date_range: Whether to ignore date range constraints
        mark_for_site: Whether to mark fetched papers for website inclusion
        db: Database instance (will create one if None)
        
    Returns:
        List of paper IDs that were successfully fetched and added
    """
    logger.info("Starting paper fetching process")
    
    # Initialize database if not provided
    if db is None:
        try:
            db = SupabaseDB()
            logger.info("Supabase DB initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            return []

    # Create API client
    semantic_scholar_api = SemanticScholarAPI(api_key=None, development_mode=False)
    logger.info("Semantic Scholar API initialized")
    
    # Get papers to process
    papers_to_fetch = []
    if paper_id:
        # Get paper by ID from Semantic Scholar
        logger.info(f"Fetching paper with ID: {paper_id}")
        paper = semantic_scholar_api.get_paper_by_id(paper_id)
        if paper:
            papers_to_fetch = [paper]
        else:
            logger.error(f"Paper with ID {paper_id} not found")
            return []
    else:
        # Get papers from Semantic Scholar based on query
        logger.info(f"Searching for papers with query: {query}")
        papers = semantic_scholar_api.get_relevant_papers(
            query=query, 
            months=months,
            limit=limit,
            ignore_date_range=ignore_date_range
        )
        papers_to_fetch = papers
    
    if not papers_to_fetch:
        logger.error("No papers found to fetch")
        return []
    
    logger.info(f"Found {len(papers_to_fetch)} papers to fetch")
    
    # Process each paper and add to database
    successfully_added = []
    skipped_papers = 0
    
    for paper in papers_to_fetch:
        paper_id = paper['paperId']
        logger.info(f"Processing paper: {paper['title']} (ID: {paper_id})")
        
        # Check if paper already exists in the database
        existing_paper = db.get_paper_by_id(paper_id)
        if existing_paper:
            logger.info(f"Paper {paper_id} already exists in database, skipping")
            skipped_papers += 1
            continue
        
        try:
            # Prepare paper data for database
            entry = {
                'id': paper_id,
                'title': paper.get('title', ''),
                'authors': [author.get('name', '') for author in paper.get('authors', [])],
                'year': paper.get('year'),
                'abstract': paper.get('abstract', ''),
                'url': paper.get('url', ''),
                'venue': paper.get('venue', ''),
                'submitted_date': paper.get('publicationDate', '').split('T')[0] if paper.get('publicationDate') else None,
                'include_on_website': mark_for_site,
                'post_to_bots': False,
                'highlight': False,
                'tldr': paper.get('tldr', {}).get('text', '') if isinstance(paper.get('tldr'), dict) else paper.get('tldr', '')
            }
            
            # Add to Supabase
            db.add_paper(entry)
            logger.info(f"Added paper to database: {paper_id}")
            successfully_added.append(paper_id)
            
        except Exception as e:
            logger.error(f"Error processing paper {paper_id}: {e}")
    
    logger.info(f"Successfully added {len(successfully_added)} papers to the database")
    if skipped_papers > 0:
        logger.info(f"Skipped {skipped_papers} papers that were already in the database")
    
    return successfully_added

def process_papers(paper_id=None, limit=5, skip_figures=False, 
                  skip_summary=False, skip_markdown=False, db=None):
    """
    Process papers that are marked for website inclusion.
    
    Args:
        paper_id: Specific paper ID to process (optional)
        limit: Maximum number of papers to process
        skip_figures: Whether to skip figure extraction
        skip_summary: Whether to skip summary generation
        skip_markdown: Whether to skip markdown generation
        db: Database instance (will create one if None)
        
    Returns:
        List of paper IDs that were successfully processed
    """
    logger.info("Starting paper processing")
    
    # Load configuration
    config = load_config()
    
    # Initialize database if not provided
    if db is None:
        try:
            db = SupabaseDB()
            logger.info("Supabase DB initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            return []

    # Initialize summarizer
    paper_summarizer = PaperSummarizer(db=db)
    logger.info("Paper summarizer initialized")
    
    # Get papers to process
    papers_to_process = []
    
    if paper_id:
        # Get specific paper from Supabase
        logger.info(f"Fetching paper with ID: {paper_id}")
        paper_data = db.get_paper_by_id(paper_id)
        if paper_data:
            papers_to_process = [paper_data]
        else:
            logger.error(f"Paper with ID {paper_id} not found in database")
            return []
    else:
        # Get papers marked for website inclusion
        try:
            papers_data = db.get_papers_to_post()
            if limit and limit > 0:
                papers_data = papers_data[:limit]
            papers_to_process = papers_data
            logger.info(f"Found {len(papers_to_process)} papers marked for website inclusion")
        except Exception as e:
            logger.error(f"Error fetching papers to process: {e}")
            return []
    
    if not papers_to_process:
        logger.info("No papers found to process")
        return []
    
    # Process each paper
    successfully_processed = []
    for paper_data in papers_to_process:
        paper_id = paper_data['id']
        logger.info(f"Processing paper: {paper_data['title']} (ID: {paper_id})")
        
        try:
            # Set data folder
            data_dir = Path(config.get('data_dir', 'data'))
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create Article object
            article = Article(
                uid=paper_id,
                title=paper_data.get('title', ''),
                url=paper_data.get('url', ''),
                authors=paper_data.get('authors', []),
                abstract=paper_data.get('abstract', ''),
                venue=paper_data.get('venue', ''),
                submitted_date=paper_data.get('submitted_date'),
                website_content_path=WEBSITE_CONTENT_PATH,
                data_folder=data_dir / paper_id
            )
            
            # Add TLDR if available
            if paper_data.get('tldr'):
                article.set_tldr(paper_data.get('tldr', ''))
            
            # Create post folder
            post = Post(article)
            post_dir = post.post_dir
            post_dir.mkdir(parents=True, exist_ok=True)
            
            # First generate summary, as we'll need it to know which figures to keep
            if not skip_summary:
                logger.info(f"Generating summary for paper: {paper_id}")
                try:
                    # Download PDF
                    article.download_pdf()
                    
                    # Generate summary
                    summary_result = paper_summarizer.summarize(article)
                    
                    if isinstance(summary_result, tuple) and len(summary_result) >= 3:
                        summary, display_figures, thumbnail_figure = summary_result
                        success = True
                    elif isinstance(summary_result, dict):
                        success = summary_result.get('success', False)
                        summary = summary_result.get('summary', '')
                        display_figures = summary_result.get('display_figures', [])
                        thumbnail_figure = summary_result.get('thumbnail_figure') or (display_figures[0] if display_figures else None)
                    else:
                        success = bool(summary_result)
                        summary = str(summary_result) if summary_result else ''
                        display_figures = []
                        thumbnail_figure = None
                    
                    if success and summary:
                        # Update the post object with summary information
                        post.summary = summary
                        post.display_figures = display_figures
                        post.thumbnail_figure = thumbnail_figure
                        
                        # Save summary to file
                        post.save_summary()
                        
                        # Store summary in Supabase
                        db.add_summary(paper_id, summary, display_figures, thumbnail_figure)
                        logger.info(f"Summary generated for paper {paper_id} with {len(display_figures)} display figures")
                    else:
                        logger.error(f"Failed to generate valid summary for paper {paper_id}")
                except Exception as e:
                    logger.error(f"Error generating summary for paper {paper_id}: {e}")
                    logger.exception("Summary generation error details:")
                    return False
            else:
                # Try to load summary from Supabase if we're skipping generation
                summary_data = db.get_summary(paper_id)
                if summary_data:
                    post.summary = summary_data.get('summary', '')
                    post.display_figures = summary_data.get('display_figures', [])
                    post.thumbnail_figure = summary_data.get('thumbnail_figure')
                    logger.info(f"Loaded existing summary for paper {paper_id}")
                else:
                    logger.warning(f"No existing summary found for paper {paper_id}")
            
            # Now extract figures, but only process the ones needed for the summary
            if not skip_figures and (post.display_figures or not post.summary):
                logger.info(f"Extracting figures for paper: {paper_id}")
                try:
                    # Initialize FigureExtractorManager
                    figure_extractor = FigureExtractorManager()
                    
                    # Extract all figures
                    success = figure_extractor.extract_figures(post)
                    
                    if success and post.figures:
                        logger.info(f"Extracted {len(post.figures)} figures for paper {paper_id}")
                        
                        # If we have a summary, only process and upload the figures needed
                        if post.display_figures:
                            # Upload only the figures mentioned in the summary and thumbnail
                            figures_to_upload = []
                            figures_to_process = set(post.display_figures)
                            if post.thumbnail_figure and post.thumbnail_figure not in figures_to_process:
                                figures_to_process.add(post.thumbnail_figure)
                            
                            for fig_id in figures_to_process:
                                if fig_id in post.figures:
                                    figure = post.figures[fig_id]
                                    # Get image data from file
                                    image_path = figure.image_path or Path(post.article.data_folder) / "figures" / f"{fig_id}.png"
                                    if image_path.exists():
                                        with open(image_path, 'rb') as f:
                                            image_data = f.read()
                                        
                                        figures_to_upload.append({
                                            'figure_id': fig_id,
                                            'image_data': image_data,
                                            'caption': figure.caption,
                                            'content_type': 'image/png'
                                        })
                            
                            # Batch upload needed figures to R2/Supabase
                            if figures_to_upload:
                                db.add_figures_batch(paper_id, figures_to_upload)
                                logger.info(f"Uploaded {len(figures_to_upload)} figures to R2 for paper {paper_id}")
                        else:
                            # If no specific figures mentioned, process all
                            figure_extractor.process_post_figures(post)
                            logger.info(f"Processed all figures for paper {paper_id}")
                    else:
                        logger.warning(f"No figures were extracted for paper {paper_id}")
                except Exception as e:
                    logger.error(f"Error extracting figures for paper {paper_id}: {e}")
                    logger.exception("Figure extraction error details:")
            
            # Generate markdown post
            if not skip_markdown:
                logger.info(f"Generating markdown post for paper: {paper_id}")
                try:
                    # Set up figure URLs if available
                    figure_urls = {}
                    if post.display_figures:
                        for fig_id in post.display_figures:
                            figure_info = db.get_figure_info(paper_id, fig_id)
                            if figure_info and figure_info.get('remote_path'):
                                figure_urls[fig_id] = figure_info['remote_path']
                    
                    # Generate markdown
                    index_path = generate_simple_markdown(article, post.summary, figure_urls, post_dir)
                    logger.info(f"Generated markdown post at {index_path}")
                    
                    # Process thumbnail
                    if post.thumbnail_figure:
                        # Set the thumbnail if available
                        try:
                            if post.thumbnail_figure in figure_urls:
                                # Download from R2
                                thumbnail_url = figure_urls[post.thumbnail_figure]
                                thumbnail_path = post_dir / "thumbnail.png"
                                
                                response = requests.get(thumbnail_url, stream=True, timeout=30)
                                if response.status_code == 200:
                                    with open(thumbnail_path, 'wb') as f:
                                        for chunk in response.iter_content(chunk_size=8192):
                                            f.write(chunk)
                                    logger.info(f"Downloaded thumbnail from R2: {thumbnail_path}")
                            else:
                                # Try to use local thumbnail
                                post.set_thumbnail()
                                logger.info("Set thumbnail from local files")
                        except Exception as e:
                            logger.error(f"Error setting thumbnail: {e}")
                except Exception as e:
                    logger.error(f"Error generating markdown post for paper {paper_id}: {e}")
                    logger.exception("Markdown generation error details:")
            
            # Mark paper as processed
            db.mark_as_posted(paper_id)
            logger.info(f"Marked paper {paper_id} as processed")
            
            # Add to successfully processed list
            successfully_processed.append(paper_id)
            
        except Exception as e:
            logger.error(f"Error processing paper {paper_id}: {e}")
            logger.exception("Full traceback:")
    
    logger.info(f"Successfully processed {len(successfully_processed)} papers")
    return successfully_processed

def generate_simple_markdown(article, summary, figure_urls, post_dir):
    """Generate a simple markdown post for the article."""
    # Format frontmatter
    author_list = article.authors if isinstance(article.authors, list) else []
    quoted_authors = [f'"{author.strip()}"' for author in author_list]
    
    frontmatter = f"""---
title: "{article.title}"
description: "{article.abstract[:200] + '...' if len(article.abstract) > 200 else article.abstract}"
authors: [{', '.join(quoted_authors)}]
date: {datetime.now().strftime('%Y-%m-%d')}
paper_url: "{article.url}"
---

# {article.title}

"""
    
    # Add summary
    content = frontmatter + summary
    
    # Add figure references
    if figure_urls:
        content += "\n\n## Figures\n\n"
        for fig_id, url in figure_urls.items():
            content += f"![{fig_id}]({url})\n\n"
    
    # Save markdown
    index_path = post_dir / "index.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return index_path

def main():
    """Main entry point with command-line argument handling."""
    parser = argparse.ArgumentParser(description='AI Safety Papers Pipeline')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Fetch papers command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch new papers')
    fetch_parser.add_argument('--paper-id', type=str, help='Fetch a specific paper by ID')
    fetch_parser.add_argument('--query', type=str, default='AI Safety', help='Search query for Semantic Scholar')
    fetch_parser.add_argument('--months', type=int, default=3, help='Months of papers to look back')
    fetch_parser.add_argument('--limit', type=int, default=10, help='Number of papers to fetch')
    fetch_parser.add_argument('--ignore-date-range', action='store_true', help='Ignore date range')
    fetch_parser.add_argument('--mark-for-site', action='store_true', help='Mark papers for inclusion on website')
    
    # Process papers command
    process_parser = subparsers.add_parser('process', help='Process papers marked for website inclusion')
    process_parser.add_argument('--paper-id', type=str, help='Process a specific paper by ID')
    process_parser.add_argument('--limit', type=int, default=5, help='Number of papers to process')
    process_parser.add_argument('--skip-figures', action='store_true', help='Skip figure extraction')
    process_parser.add_argument('--skip-summary', action='store_true', help='Skip summary generation')
    process_parser.add_argument('--skip-markdown', action='store_true', help='Skip markdown generation')
    
    # Full pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Run the full pipeline (fetch and process)')
    pipeline_parser.add_argument('--paper-id', type=str, help='Process a specific paper by ID')
    pipeline_parser.add_argument('--query', type=str, default='AI Safety', help='Search query for Semantic Scholar')
    pipeline_parser.add_argument('--months', type=int, default=3, help='Months of papers to look back')
    pipeline_parser.add_argument('--limit', type=int, default=5, help='Number of papers to fetch and process')
    pipeline_parser.add_argument('--ignore-date-range', action='store_true', help='Ignore date range')
    pipeline_parser.add_argument('--skip-figures', action='store_true', help='Skip figure extraction')
    pipeline_parser.add_argument('--skip-summary', action='store_true', help='Skip summary generation')
    pipeline_parser.add_argument('--skip-markdown', action='store_true', help='Skip markdown generation')
    
    args = parser.parse_args()
    
    # Initialize database once for all operations
    try:
        db = SupabaseDB()
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {e}")
        return 1

    # Handle commands
    if args.command == 'fetch':
        fetch_papers(
            paper_id=args.paper_id,
            query=args.query,
            months=args.months,
            limit=args.limit,
            ignore_date_range=args.ignore_date_range,
            mark_for_site=args.mark_for_site,
            db=db
        )
        
    elif args.command == 'process':
        process_papers(
            paper_id=args.paper_id,
            limit=args.limit,
            skip_figures=args.skip_figures,
            skip_summary=args.skip_summary,
            skip_markdown=args.skip_markdown,
            db=db
        )
        
    elif args.command == 'pipeline':
        # Run both functions in sequence
        if args.paper_id:
            # Process a specific paper
            fetch_results = fetch_papers(
                paper_id=args.paper_id,
                mark_for_site=True,
                db=db
            )
        else:
            # Fetch and process multiple papers
            fetch_results = fetch_papers(
                query=args.query,
                months=args.months,
                limit=args.limit,
                ignore_date_range=args.ignore_date_range,
                mark_for_site=False,
                db=db
            )
        
            # Process the papers we just fetched if explicitly requested
            # or process any other papers marked for inclusion on the website that haven't been processed yet
            process_papers(
                limit=args.limit,
                skip_figures=args.skip_figures,
                skip_summary=args.skip_summary,
                skip_markdown=args.skip_markdown,
                db=db
            )
    else:
        parser.print_help()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
