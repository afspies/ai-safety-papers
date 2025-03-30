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
import re

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

def fetch_papers(paper_id=None, query="AI Safety", months=3, years=None, limit=10, 
                ignore_date_range=False, mark_for_site=False, db=None,
                page_size=None, max_pages=None):
    """
    Fetch papers from Semantic Scholar and store them in the database.
    
    Args:
        paper_id: Specific paper ID to fetch (optional)
        query: Search query for Semantic Scholar
        months: Number of months to look back
        years: Number of years to look back (overrides months if provided)
        limit: Maximum number of papers to fetch (when not using pagination)
        ignore_date_range: Whether to ignore date range constraints
        mark_for_site: Whether to mark fetched papers for website inclusion
        db: Database instance (will create one if None)
        page_size: Size of each pagination page (if None, uses default of API)
        max_pages: Maximum number of pages to fetch (if None, fetches all available)
        
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
        
        # Convert years to months if specified
        if years is not None:
            months = years * 12
            logger.info(f"Using {years} years ({months} months) for date range")
        
        if page_size and max_pages:
            # Use pagination to fetch papers
            logger.info(f"Using pagination with page_size={page_size}, max_pages={max_pages}")
            papers = []
            page = 1
            total_fetched = 0
            
            while page <= max_pages:
                logger.info(f"Fetching page {page} of results")
                page_results = semantic_scholar_api.get_relevant_papers(
                    query=query, 
                    months=months,
                    limit=page_size,
                    offset=(page - 1) * page_size,
                    ignore_date_range=ignore_date_range
                )
                
                if not page_results:
                    logger.info(f"No more results found after page {page-1}")
                    break
                
                papers.extend(page_results)
                total_fetched += len(page_results)
                logger.info(f"Retrieved {len(page_results)} papers, total: {total_fetched}")
                
                # If we got fewer results than the page size, we've reached the end
                if len(page_results) < page_size:
                    break
                
                page += 1
                
            papers_to_fetch = papers
            logger.info(f"Fetched a total of {len(papers_to_fetch)} papers across {page} pages")
        else:
            # Standard fetch without pagination
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

def process_paper_figures(post, paper_id, db, figure_extractor, skip_figures=False):
    """
    Process figures for a paper - handles both extraction and storage in R2.
    Used by both main processing and reprocessing workflows.
    
    Args:
        post: Post object containing the article
        paper_id: The paper ID
        db: Database instance
        figure_extractor: FigureExtractorManager instance
        skip_figures: Whether to skip figure extraction
        
    Returns:
        Dictionary of figure_urls mapping figure IDs to their URLs
    """
    figure_urls = {}
    
    # Don't do anything if we're skipping figures
    if skip_figures:
        logger.info(f"Skipping figure extraction for paper: {paper_id}")
        return figure_urls
    
    logger.info(f"Processing figures for paper: {paper_id}")
    try:
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
                # If no specific figures mentioned, process all figures using the manager
                figure_extractor.store_figures_in_r2(post)
                logger.info(f"Processed all figures for paper {paper_id} using the figure manager")
                
            # Get figure URLs for generating markdown
            if post.display_figures:
                for fig_id in post.display_figures:
                    figure_info = db.get_figure_info(paper_id, fig_id)
                    if figure_info and figure_info.get('remote_path'):
                        figure_urls[fig_id] = figure_info['remote_path']
                        
            # Special handling for parent figures with subfigures
            # Get figure metadata to check for parent-subfigure relationships
            figures_dir = post.article.data_folder / "figures"
            figures_meta = figure_extractor._load_figure_metadata(figures_dir)
            
            # Identify parent figures that only have subfigures
            parent_figures = figure_extractor._identify_parent_figures(figures_meta, post.figures)
            
            # For each parent with only subfigures, get all subfigure URLs
            for parent_id in parent_figures.keys():
                # Extract the numeric part (e.g., "fig1" -> "1")
                if parent_id.startswith('fig'):
                    parent_num = parent_id[3:]
                    
                    # If we don't already have a URL for this parent figure
                    if parent_num not in figure_urls:
                        # Find all subfigures for this parent
                        subfig_urls = {}
                        
                        # First look for subfigures with the format "parent_num.letter"
                        for fig_id in post.display_figures:
                            if '.' in fig_id and fig_id.split('.')[0] == parent_num:
                                figure_info = db.get_figure_info(paper_id, f"fig{fig_id.replace('.', '_')}")
                                if figure_info and figure_info.get('remote_path'):
                                    subfig_urls[fig_id] = figure_info['remote_path']
                        
                        # If we found subfigures, store their URLs with the parent key
                        if subfig_urls:
                            figure_urls[f"subfigures_{parent_num}"] = subfig_urls
        else:
            logger.warning(f"No figures were extracted for paper {paper_id}")
            
    except Exception as e:
        logger.error(f"Error extracting figures for paper {paper_id}: {e}")
        logger.exception("Figure extraction error details:")
    
    return figure_urls

def generate_markdown_post(article, post, figure_urls, post_dir):
    """
    Generate a markdown post with proper figure handling.
    Used by both main processing and reprocessing workflows.
    
    Args:
        article: Article object
        post: Post object with summary and figure information
        figure_urls: Dictionary mapping figure IDs to figure URLs
        post_dir: Directory to save the post
        
    Returns:
        Path to the generated markdown file
    """
    logger.info(f"Generating markdown post for paper: {article.uid}")
    try:
        # Generate markdown
        index_path = generate_simple_markdown(article, post.summary, figure_urls, post_dir)
        logger.info(f"Generated markdown post at {index_path}")
        
        # Process thumbnail
        if post.thumbnail_figure:
            # Set the thumbnail if available
            try:
                # First check if this thumbnail is a subfigure
                thumbnail_id = post.thumbnail_figure
                thumbnail_url = figure_urls.get(thumbnail_id)
                
                if thumbnail_url:
                    # Download from R2
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
                
        return index_path
    except Exception as e:
        logger.error(f"Error generating markdown post: {e}")
        logger.exception("Markdown generation error details:")
        return None

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
    
    # Initialize figure extractor
    figure_extractor = FigureExtractorManager()
    logger.info("Figure extractor initialized")
    
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
                    
                    # Check if display_figures is empty but should have values
                    if post.summary and not post.display_figures:
                        logger.info(f"Summary exists but display_figures is empty for paper {paper_id}, extracting figures")
                        post.display_figures = paper_summarizer._extract_figures_from_summary(post.summary)
                        
                        if post.display_figures:
                            # If we found figures, update the database
                            db.add_summary(
                                paper_id,
                                post.summary,
                                post.display_figures,
                                post.thumbnail_figure
                            )
                            logger.info(f"Extracted and updated {len(post.display_figures)} display figures for paper {paper_id}")
                else:
                    logger.warning(f"No existing summary found for paper {paper_id}")
            
            # Process figures and get URLs
            figure_urls = process_paper_figures(post, paper_id, db, figure_extractor, skip_figures)
            
            # Generate markdown post
            if not skip_markdown:
                generate_markdown_post(article, post, figure_urls, post_dir)
            
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

def reprocess_papers_with_incomplete_data(paper_id=None, limit=5, skip_figures=False, db=None):
    """
    Reprocess papers that are marked for website inclusion but have missing markdown_summary
    or empty display_figures, even if they've been already marked as posted.
    
    This function does NOT re-query the LLM endpoint, but instead regenerates missing data
    from existing summaries.
    
    Args:
        paper_id: Specific paper ID to reprocess (optional)
        limit: Maximum number of papers to reprocess
        skip_figures: Whether to skip figure extraction
        db: Database instance (will create one if None)
        
    Returns:
        List of paper IDs that were successfully reprocessed
    """
    logger.info("Starting reprocessing of papers with incomplete data")
    
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
    
    # Initialize figure extractor
    figure_extractor = FigureExtractorManager()
    logger.info("Figure extractor initialized")
    
    # Get papers to reprocess
    papers_to_reprocess = []
    
    if paper_id:
        # Get specific paper from Supabase
        logger.info(f"Fetching paper with ID: {paper_id}")
        paper_data = db.get_paper_by_id(paper_id)
        if paper_data:
            papers_to_reprocess = [paper_data]
        else:
            logger.error(f"Paper with ID {paper_id} not found in database")
            return []
    else:
        # Get papers needing reprocessing
        try:
            papers_data = db.get_papers_needing_reprocessing()
            if limit and limit > 0:
                papers_data = papers_data[:limit]
            papers_to_reprocess = papers_data
            logger.info(f"Found {len(papers_to_reprocess)} papers needing reprocessing")
        except Exception as e:
            logger.error(f"Error fetching papers to reprocess: {e}")
            return []
    
    if not papers_to_reprocess:
        logger.info("No papers found to reprocess")
        return []
    
    # Process each paper
    successfully_reprocessed = []
    for paper_data in papers_to_reprocess:
        paper_id = paper_data['id']
        logger.info(f"Reprocessing paper: {paper_data['title']} (ID: {paper_id})")
        
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
            
            # Get existing summary from Supabase
            summary_data = db.get_summary(paper_id)
            
            # Check if we need to regenerate the summary data
            if summary_data and summary_data.get('summary'):
                summary = summary_data.get('summary', '')
                
                # Extract display_figures if they're missing or empty
                if not summary_data.get('display_figures'):
                    logger.info(f"Regenerating display_figures for paper {paper_id}")
                    # Use the PaperSummarizer method to extract figures
                    figures = paper_summarizer._extract_figures_from_summary(summary)
                    
                    # Update the summary data
                    display_figures = figures
                    logger.info(f"Extracted {len(display_figures)} figure references from summary")
                else:
                    # Use existing figures
                    display_figures = summary_data.get('display_figures', [])
                    
                # Get thumbnail figure
                thumbnail_figure = summary_data.get('thumbnail_figure')
                if not thumbnail_figure and display_figures:
                    # Use the first figure as thumbnail if none is specified
                    thumbnail_figure = display_figures[0]
                    logger.info(f"Using first figure {thumbnail_figure} as thumbnail")
                
                # Generate markdown summary if missing
                if not summary_data.get('markdown_summary'):
                    logger.info(f"Generating markdown summary for paper {paper_id}")
                    markdown_summary = paper_summarizer.post_process_summary_to_markdown(paper_id, summary)
                    logger.info(f"Generated markdown summary of length {len(markdown_summary)}")
                else:
                    # Use existing markdown
                    markdown_summary = summary_data.get('markdown_summary', '')
                
                # Update the summary in Supabase with all the data
                db.add_summary(
                    paper_id, 
                    summary, 
                    display_figures, 
                    thumbnail_figure,
                    markdown_summary
                )
                logger.info(f"Updated summary data in Supabase for paper {paper_id}")
                
                # Update the post object with summary information
                post.summary = summary
                post.display_figures = display_figures
                post.thumbnail_figure = thumbnail_figure
                
                # Save summary to file
                post.save_summary()
            else:
                logger.error(f"No existing summary found for paper {paper_id}, cannot reprocess")
                continue
            
            # Process figures and get URLs using the shared function
            figure_urls = process_paper_figures(post, paper_id, db, figure_extractor, skip_figures)
            
            # Special handling for paper 02ad427b0d20fb976741e332f69c2fd00c751164
            if paper_id == "02ad427b0d20fb976741e332f69c2fd00c751164":
                logger.info("Applying special handling for paper 02ad427b0d20fb976741e332f69c2fd00c751164")
                # Manually replace any remaining <FIGURE_ID> tags
                
                # Get figure URLs
                fig1a_url = db.get_figure_url(paper_id, "fig1_a")
                fig1b_url = db.get_figure_url(paper_id, "fig1_b")
                
                if fig1a_url and fig1b_url:
                    logger.info(f"Found URLs for fig1_a and fig1_b: {fig1a_url}, {fig1b_url}")
                    
                    # Replace <FIGURE_ID>1</FIGURE_ID> with actual figure images
                    pattern = r'<FIGURE_ID>1</FIGURE_ID>'
                    replacement = f"\n\n**Figure 1**\n\n![Figure 1.a]({fig1a_url})\n\n![Figure 1.b]({fig1b_url})\n\n"
                    
                    # Apply the replacement to the summary
                    post.summary = re.sub(pattern, replacement, post.summary, count=1)
                    # Replace other occurrences with bold text
                    post.summary = re.sub(pattern, "**Figure 1**", post.summary)
                    
                    # Save modified summary
                    post.save_summary()
                    logger.info("Manually replaced Figure 1 tags in the summary")
                
                # Handle other figures similarly
                fig3a_url = db.get_figure_url(paper_id, "fig3_a")
                fig3b_url = db.get_figure_url(paper_id, "fig3_b")
                fig3c_url = db.get_figure_url(paper_id, "fig3_c")
                
                if fig3a_url and fig3b_url and fig3c_url:
                    pattern = r'<FIGURE_ID>3\.a</FIGURE_ID>'
                    replacement = f"\n\n**Figure 3**\n\n![Figure 3.a]({fig3a_url})\n\n![Figure 3.b]({fig3b_url})\n\n![Figure 3.c]({fig3c_url})\n\n"
                    post.summary = re.sub(pattern, replacement, post.summary, count=1)
                    post.summary = re.sub(pattern, "**Figure 3.a**", post.summary)
                    post.summary = re.sub(pattern, "**Figure 3.a**", post.summary)
                    post.save_summary()
            
            # Generate markdown post using the shared function
            generate_markdown_post(article, post, figure_urls, post_dir)
            
            # Add to successfully reprocessed list
            successfully_reprocessed.append(paper_id)
            
        except Exception as e:
            logger.error(f"Error reprocessing paper {paper_id}: {e}")
            logger.exception("Full traceback:")
    
    logger.info(f"Successfully reprocessed {len(successfully_reprocessed)} papers")
    return successfully_reprocessed

def generate_simple_markdown(article, summary, figure_urls, post_dir):
    """Generate a simple markdown post for the article with proper handling of subfigures."""
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
    
    # Add summary with proper figure handling
    content = frontmatter
    
    # Process summary text to replace figure references
    # First prepare a dictionary of parent figures that have subfigures
    parent_subfigure_mapping = {}
    for key, value in figure_urls.items():
        if key.startswith('subfigures_'):
            parent_num = key.split('_')[1]
            parent_subfigure_mapping[parent_num] = value
    
    # Process the summary text to replace figure tags
    processed_summary = summary
    
    # First replace parent figures that have subfigures
    for parent_num, subfig_urls in parent_subfigure_mapping.items():
        pattern = rf'<FIGURE_ID>{parent_num}</FIGURE_ID>'
        replacement = f"\n\n**Figure {parent_num}**\n\n"
        
        # Add each subfigure
        for subfig_id, url in subfig_urls.items():
            subfig_letter = subfig_id.split('.')[1] if '.' in subfig_id else ''
            subfig_display = f"Figure {parent_num}.{subfig_letter}" if subfig_letter else f"Figure {parent_num}"
            replacement += f"![{subfig_display}]({url})\n\n"
        
        # Replace the first occurrence with the full subfigure set
        processed_summary = re.sub(pattern, replacement, processed_summary, count=1)
        
        # Replace remaining occurrences with just the bold text
        processed_summary = re.sub(pattern, f"**Figure {parent_num}**", processed_summary)
    
    # Now handle regular figures
    figure_refs = re.findall(r'<FIGURE_ID>(\d+)(\.([a-zA-Z]))?\</FIGURE_ID>', processed_summary)
    for ref in figure_refs:
        fig_num = ref[0]
        subfig_letter = ref[2]  # Will be empty for main figures
        
        # Form the figure ID for lookup in figure_urls
        fig_id = f"{fig_num}.{subfig_letter.lower()}" if subfig_letter else fig_num
        
        # Create the display text
        display_text = f"Figure {fig_num}"
        if subfig_letter:
            display_text = f"Figure {fig_num}.{subfig_letter}"
        
        # Replace the tag
        pattern = rf'<FIGURE_ID>{fig_num}(\.{subfig_letter})?\</FIGURE_ID>'
        
        # Check if we have a URL for this figure
        if fig_id in figure_urls:
            url = figure_urls[fig_id]
            # Add the figure image after the reference
            replacement = f"**{display_text}**\n\n![{display_text}]({url})\n\n"
            processed_summary = re.sub(pattern, replacement, processed_summary, count=1)
        else:
            # Just replace with bold text if no URL is available
            replacement = f"**{display_text}**"
            processed_summary = re.sub(pattern, replacement, processed_summary)
    
    content += processed_summary
    
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
    fetch_parser.add_argument('--years', type=int, help='Years of papers to look back (overrides months if provided)')
    fetch_parser.add_argument('--limit', type=int, default=10, help='Number of papers to fetch (when not using pagination)')
    fetch_parser.add_argument('--ignore-date-range', action='store_true', help='Ignore date range')
    fetch_parser.add_argument('--mark-for-site', action='store_true', help='Mark papers for inclusion on website')
    fetch_parser.add_argument('--page-size', type=int, help='Size of each pagination page')
    fetch_parser.add_argument('--max-pages', type=int, help='Maximum number of pages to fetch')
    
    # Process papers command
    process_parser = subparsers.add_parser('process', help='Process papers marked for website inclusion')
    process_parser.add_argument('--paper-id', type=str, help='Process a specific paper by ID')
    process_parser.add_argument('--limit', type=int, default=5, help='Number of papers to process')
    process_parser.add_argument('--skip-figures', action='store_true', help='Skip figure extraction')
    process_parser.add_argument('--skip-summary', action='store_true', help='Skip summary generation')
    process_parser.add_argument('--skip-markdown', action='store_true', help='Skip markdown generation')
    
    # Reprocess incomplete data command
    reprocess_parser = subparsers.add_parser('reprocess', help='Reprocess papers with missing markdown summary or empty figure list')
    reprocess_parser.add_argument('--paper-id', type=str, help='Reprocess a specific paper by ID')
    reprocess_parser.add_argument('--limit', type=int, default=5, help='Number of papers to reprocess')
    reprocess_parser.add_argument('--skip-figures', action='store_true', help='Skip figure extraction')
    
    # Full pipeline command
    pipeline_parser = subparsers.add_parser('pipeline', help='Run the full pipeline (fetch and process)')
    pipeline_parser.add_argument('--paper-id', type=str, help='Process a specific paper by ID')
    pipeline_parser.add_argument('--query', type=str, default='AI Safety', help='Search query for Semantic Scholar')
    pipeline_parser.add_argument('--months', type=int, default=3, help='Months of papers to look back')
    pipeline_parser.add_argument('--years', type=int, help='Years of papers to look back (overrides months if provided)')
    pipeline_parser.add_argument('--limit', type=int, default=5, help='Number of papers to fetch and process')
    pipeline_parser.add_argument('--ignore-date-range', action='store_true', help='Ignore date range')
    pipeline_parser.add_argument('--page-size', type=int, help='Size of each pagination page')
    pipeline_parser.add_argument('--max-pages', type=int, help='Maximum number of pages to fetch')
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
            years=args.years,
            limit=args.limit,
            ignore_date_range=args.ignore_date_range,
            mark_for_site=args.mark_for_site,
            page_size=args.page_size,
            max_pages=args.max_pages,
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
        
    elif args.command == 'reprocess':
        reprocess_papers_with_incomplete_data(
            paper_id=args.paper_id,
            limit=args.limit,
            skip_figures=args.skip_figures,
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
                years=args.years,
                limit=args.limit,
                ignore_date_range=args.ignore_date_range,
                mark_for_site=False,
                page_size=args.page_size,
                max_pages=args.max_pages,
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
