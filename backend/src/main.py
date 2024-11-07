import sys
import os
import time
import logging
from utils.config_loader import load_config
from api.semantic_scholar import SemanticScholarAPI
from sheets.sheets_db import SheetsDB
from datetime import datetime
import argparse
from summarizer.paper_summarizer import PaperSummarizer
from models.article import Article
import shutil
from pathlib import Path
import re

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up logging
DEBUG_MODE = True  # Set this to False to disable debug logs

def setup_logging():
    log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Filter out noisy loggers
    logging.getLogger('pdfminer').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore.http11').setLevel(logging.WARNING)
    logging.getLogger('papermage').setLevel(logging.WARNING)
    logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
    logging.getLogger('anthropic._base_client').setLevel(logging.WARNING)

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
    
    # Get existing paper IDs from the database first
    existing_papers = set()
    try:
        all_records = db.worksheet.get_all_records()
        existing_papers = {row['Paper ID'] for row in all_records if row['Paper ID']}
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
            db.add_entry(entry)
            logger.debug(f"Successfully processed paper: {paper['paperId']}")
            
        except Exception as e:
            logger.error(f"Failed to process paper {paper.get('paperId', 'unknown')}: {e}")
            logger.exception("Full traceback:")
            continue
    
    logger.debug(f"Processed {len(all_papers)} new papers in total")

def process_flagged_papers(db: SheetsDB):
    logger = logging.getLogger(__name__)
    logger.info("Starting process_flagged_papers")
    
    try:
        logger.debug("Loading config...")
        config = load_config()
        logger.debug(f"Available config keys: {list(config.keys())}")
        
        logger.debug("Getting papers to post...")
        papers_to_post = db.get_papers_to_post()
        logger.debug(f"Found {len(papers_to_post)} papers to post")
        
        logger.debug("Setting up website content path...")
        website_content_path = Path(config.get('website', {}).get('content_path', '../ai-safety-site/content/en'))
        logger.debug(f"Using website content path: {website_content_path}")
        
        posts_path = website_content_path / "posts"
        logger.debug(f"Creating posts directory at: {posts_path}")
        posts_path.mkdir(parents=True, exist_ok=True)
        
        logger.debug("Initializing PaperSummarizer...")
        summarizer = PaperSummarizer(config['anthropic']['api_key'])
        logger.debug("PaperSummarizer initialized successfully")
        
        for i, paper in enumerate(papers_to_post):
            logger.info(f"Processing paper {i+1}/{len(papers_to_post)}: {paper.get('id', 'unknown id')}")
            try:
                # Create article instance
                article = create_article_instance(paper)
                
                # Set up data paths
                paper_dir = Path(config['data_dir']) / article.uid
                pdf_path = paper_dir / "paper.pdf"
                article.set_data_paths(paper_dir, pdf_path)
                
                # Download PDF - skip processing if download fails
                if not article.download_pdf():
                    logger.error(f"Skipping paper {article.uid} due to PDF download failure")
                    continue
                
                # Process figures - skip if figure processing fails
                if not article.process_figures():
                    logger.error(f"Skipping paper {article.uid} due to figure processing failure")
                    continue
                
                # Generate summary
                logger.debug("Generating summary...")
                summary, display_figures, thumbnail_figure = summarizer.summarize(article)
                logger.debug(f"Summary generated. Display figures: {display_figures}, Thumbnail: {thumbnail_figure}")
                
                # Convert display_figures from numbers to internal IDs
                internal_display_figures = [f"fig_0_{num}" for num in display_figures]
                article.set_displayed_figures(internal_display_figures)
                
                # Set thumbnail source
                if thumbnail_figure and thumbnail_figure.isdigit():
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
                
                # Create website post
                create_website_post(article, summary, posts_path)
                
                # Mark as posted
                db.mark_as_posted(paper['id'])
                logger.info(f"Successfully processed paper: {paper['id']}")
                
            except Exception as e:
                logger.error(f"Error processing paper {paper.get('id', 'unknown id')}: {e}")
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
    
    # Copy displayed figures and track which ones were successfully copied
    logger.debug(f"Processing {len(article.displayed_figures)} displayed figures")
    copied_figures = {}  # Maps internal figure IDs to actual figure IDs
    
    # Create a lookup dictionary for faster figure matching
    figure_lookup = {}
    for fig_path in article.figures.values():
        fig_basename = fig_path.stem
        # Extract the label part (e.g., "fig1" from "fig_0_1_fig1")
        label_match = re.search(r'_(fig\d+|tab\d+|unk)$', fig_basename)
        if label_match:
            label = label_match.group(1)
            # Only store the first occurrence of each label
            if label not in figure_lookup:
                figure_lookup[label] = (fig_basename, fig_path)
    
    for internal_fig_id in article.displayed_figures:
        # Extract the figure number from internal ID (e.g., "3" from "fig_0_3")
        fig_num_match = re.search(r'fig_\d+_(\d+)', internal_fig_id)
        if fig_num_match:
            fig_num = fig_num_match.group(1)
            # Look for matching figure with this number
            fig_label = f"fig{fig_num}"
            
            if fig_label in figure_lookup:
                fig_basename, fig_path = figure_lookup[fig_label]
                try:
                    # Copy the figure
                    dest_path = post_dir / f"{fig_basename}.png"
                    shutil.copy2(fig_path, dest_path)
                    copied_figures[internal_fig_id] = fig_basename
                    logger.debug(f"Copied figure {fig_basename} to {dest_path}")
                except Exception as e:
                    logger.error(f"Failed to copy figure {fig_basename}: {e}")
            else:
                logger.warning(f"No matching figure found for {fig_label}")
                copied_figures[internal_fig_id] = None
        else:
            logger.warning(f"Invalid internal figure ID format: {internal_fig_id}")
            copied_figures[internal_fig_id] = None
    
    # Create markdown post with updated figure references
    post_content = create_post_markdown(article, summary, copied_figures)
    markdown_path = post_dir / "index.md"
    logger.debug(f"Writing markdown content to {markdown_path}")
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(post_content)
    
    logger.debug(f"Created website post for paper {article.uid}")

def create_post_markdown(article: Article, summary: str, copied_figures: dict) -> str:
    """
    Generate the markdown content for the post with metadata in YAML frontmatter.
    """
    logger = logging.getLogger(__name__)
    
    # Handle case where authors might be empty
    author_list = article.authors if isinstance(article.authors, list) else []
    quoted_authors = [f'"{author.strip()}"' for author in author_list]

    # Format the frontmatter with comprehensive metadata
    frontmatter = f"""---
title: "{article.title}"
description: "{article.abstract[:200] if hasattr(article, 'abstract') else ''}"
authors: [{', '.join(quoted_authors)}]
date: {datetime.now().strftime('%Y-%m-%d')}
publication_date: {article.submitted_date.strftime('%Y-%m-%d') if hasattr(article, 'submitted_date') and article.submitted_date else 'Unknown'}
venue: "{article.venue if hasattr(article, 'venue') else ''}"
paper_url: "{article.url}"
abstract: "{article.abstract if hasattr(article, 'abstract') else ''}"
added_date: {datetime.now().strftime('%Y-%m-%d')}
bookcase_cover_src: '/posts/paper_{article.uid}/thumbnail.png'
weight: 1
---
# Summary
"""
    
    # Process summary to include figure references
    content = summary
    
    # Find all figure references in the summary
    figure_pattern = r'<FIGURE_ID>(\d+)</FIGURE_ID>'
    figure_matches = re.finditer(figure_pattern, content)
    
    # Replace each figure reference
    for match in figure_matches:
        full_match = match.group(0)
        fig_num = match.group(1)
        internal_fig_id = f"fig_0_{fig_num}"
        
        logger.debug(f"Processing figure reference: {internal_fig_id} (from {full_match})")
        
        actual_fig_id = copied_figures.get(internal_fig_id)
        if actual_fig_id and actual_fig_id in article.figures:
            replacement = f'{{{{< figure src="{actual_fig_id}.png" >}}}}'
            logger.debug(f"Replacing {full_match} with Hugo shortcode using {actual_fig_id}")
        else:
            if actual_fig_id:
                label_match = re.search(r'_(fig\d+|tab\d+|unk)$', actual_fig_id)
                if label_match:
                    fig_label = label_match.group(1)
                    replacement = f'*[See {fig_label} in the original paper]*'
                else:
                    replacement = f'*[See Figure {fig_num} in the original paper]*'
            else:
                replacement = f'*[See Figure {fig_num} in the original paper]*'
            logger.warning(f"Using text replacement for missing figure {internal_fig_id}")
        
        content = content.replace(full_match, replacement)
    
    return frontmatter + content

if __name__ == "__main__":
    main()
