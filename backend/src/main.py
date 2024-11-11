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
import json

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up logging
DEBUG_MODE = True  # Set this to False to disable debug logs

# Initialize logger at the top of the file
logger = logging.getLogger(__name__)

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
            process_flagged_papers(sheets_db, args)

            logger.info("Processing cycle completed. Waiting for next cycle.")
            # Wait for the next cycle (e.g., every 24 hours)
            time.sleep(24 * 60 * 60)
    except Exception as e:
        logger.error(f"An error occurred during initialization: {e}")
        sys.exit(1)

def process_new_papers(api: SemanticScholarAPI, db: SheetsDB, ignore_date_range: bool = False, months: int = 1):
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

def process_flagged_papers(db: SheetsDB, args):
    logger.info("Starting process_flagged_papers")
    
    try:
        logger.debug("Loading config...")
        config = load_config()
        
        # Initialize API if needed for reprocessing info
        semantic_scholar_api = None
        if args.reprocess in ['info', 'all']:
            api_key = config['semantic_scholar']['api_key']
            semantic_scholar_api = SemanticScholarAPI(api_key)
            logger.debug("Initialized Semantic Scholar API for reprocessing")
        
        # Get papers based on command line args
        if args.paper_id:
            papers_to_post = [db.get_paper_by_id(args.paper_id)]
            if not papers_to_post[0]:
                logger.error(f"Paper with ID {args.paper_id} not found")
                return
        else:
            papers_to_post = db.get_papers_to_post()
            
        logger.debug(f"Found {len(papers_to_post)} papers to process")
        
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
                # Reprocess paper info if requested
                if args.reprocess in ['info', 'all']:
                    try:
                        logger.debug(f"Re-querying API for paper {paper['id']}")
                        updated_info = semantic_scholar_api.fetch_paper_details_batch([paper['id']])[0]
                        if updated_info:
                            # Update paper info while preserving existing fields
                            paper.update({
                                'title': updated_info.get('title', paper['title']),
                                'authors': [a.get('name', '') for a in updated_info.get('authors', [])],
                                'year': updated_info.get('year', paper['year']),
                                'abstract': updated_info.get('abstract', paper['abstract']),
                                'url': updated_info.get('url', paper['url']),
                                'venue': updated_info.get('venue', paper['venue']),
                                'tldr': updated_info.get('tldr', paper.get('tldr')),
                            })
                            # Update the database entry
                            db.update_entry(paper)
                            logger.info(f"Updated paper info for {paper['id']}")
                    except Exception as e:
                        logger.error(f"Failed to update paper info for {paper['id']}: {e}")
                
                # Create article instance
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
                
                # Create website post if requested or needed
                post_dir = posts_path / f"paper_{article.uid}"
                if args.reprocess in ['markdown', 'all'] or not post_dir.exists():
                    create_website_post(article, summary, posts_path)
                
                # Only mark as posted if this is a new paper
                if not args.reprocess:
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
    
    # Add TLDR if available - handle both API and database formats
    if 'tldr' in paper:
        if isinstance(paper['tldr'], dict):
            tldr_text = paper['tldr'].get('text')
        else:
            tldr_text = paper['tldr']  # Direct string from database
        if tldr_text:
            article.set_tldr(tldr_text)
            logger.debug(f"Set TLDR for article {article.uid}: {tldr_text[:100]}...")
    
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
    
    # Create a lookup dictionary for faster figure matching
    figure_lookup = {}
    for fig_id, figure_data in article.figures.items():
        if figure_data.type == 'figure':  # Only handle image figures here
            # Extract the label part (e.g., "fig1" from the fig_id)
            label_match = re.search(r'(fig\d+|tab\d+)', fig_id)
            if label_match:
                label = label_match.group(1)
                # Only store the first occurrence of each label
                if label not in figure_lookup:
                    figure_lookup[label] = (fig_id, figure_data)
    
    # Copy displayed figures and track which ones were successfully copied
    logger.debug(f"Processing {len(article.displayed_figures)} displayed figures")
    copied_figures = {}
    
    for internal_fig_id in article.displayed_figures:
        # Extract the figure number from internal ID (e.g., "3" from "fig_0_3")
        fig_num_match = re.search(r'fig_\d+_(\d+)', internal_fig_id)
        if fig_num_match:
            fig_num = fig_num_match.group(1)
            # Look for matching figure with this number
            fig_label = f"fig{fig_num}"
            
            if fig_label in figure_lookup:
                fig_id, figure_data = figure_lookup[fig_label]
                try:
                    # Copy the figure
                    dest_path = post_dir / f"{fig_id}.png"
                    shutil.copy2(figure_data.path, dest_path)
                    copied_figures[internal_fig_id] = fig_id
                    logger.debug(f"Copied figure {fig_id} to {dest_path}")
                except Exception as e:
                    logger.error(f"Failed to copy figure {fig_id}: {e}")
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

def create_post_markdown(article: Article, summary: str, copied_figures: dict) -> str:
    """Generate the markdown content for the post."""
    logger = logging.getLogger(__name__)
    
    def escape_caption(caption: str) -> str:
        """
        Escape caption text for Hugo shortcode.
        Handles quotation marks, backticks, and other special characters.
        """
        if not caption:
            return ""
            
        # Replace newlines with spaces
        caption = ' '.join(caption.splitlines())
        
        # Handle nested quotes by replacing them with single quotes
        # This preserves any existing escaped quotes
        caption = re.sub(r'(?<!\\)"', "'", caption)
        
        # Escape any remaining unescaped quotes
        caption = caption.replace('\\"', '"').replace('"', '\\"')
        
        # Escape backticks that might interfere with markdown
        caption = caption.replace('`', '\\`')
        
        # Handle other special characters that might cause issues
        caption = caption.replace('\\', '\\\\')  # Must come first
        caption = caption.replace('$', '\\$')    # For math expressions
        
        return caption
    
    # Format frontmatter with proper escaping
    author_list = article.authors if isinstance(article.authors, list) else []
    quoted_authors = [f'"{author.strip()}"' for author in author_list]

    # Get description and abstract, ensuring they're properly escaped
    description = article.abstract[:200] if hasattr(article, 'abstract') else ''
    abstract = article.abstract if hasattr(article, 'abstract') else ''
    
    # Add TLDR to frontmatter
    tldr = article.tldr if hasattr(article, 'tldr') and article.tldr else ''

    # Update the frontmatter with proper escaping and TLDR
    frontmatter = f"""---
title: "{escape_yaml(article.title)}"
description: "{escape_yaml(description)}"
authors: [{', '.join(quoted_authors)}]
date: {datetime.now().strftime('%Y-%m-%d')}
publication_date: {article.submitted_date.strftime('%Y-%m-%d') if hasattr(article, 'submitted_date') and article.submitted_date else 'Unknown'}
venue: "{escape_yaml(article.venue if hasattr(article, 'venue') else '')}"
paper_url: "{article.url}"
abstract: "{escape_yaml(abstract)}"
tldr: "{escape_yaml(tldr)}"
added_date: {datetime.now().strftime('%Y-%m-%d')}
bookcase_cover_src: '/posts/paper_{article.uid}/thumbnail.png'
math: true
katex: true
weight: 1
---

# Summary

"""
    
    # Clean LaTeX in content before processing figures
    content = clean_latex(summary)
    
    # Load figure metadata
    figures_metadata = {}
    metadata_path = article.data_folder / "figures" / "figures_metadata.json"
    try:
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                figures_metadata = json.load(f)
            logger.debug(f"Loaded figures metadata from {metadata_path}")
        else:
            logger.warning(f"No figures metadata found at {metadata_path}")
    except Exception as e:
        logger.error(f"Error loading figures metadata: {e}")
    
    # Process summary to include figures and tables with captions
    figure_pattern = r'<FIGURE_ID>(\d+)</FIGURE_ID>'
    
    for match in re.finditer(figure_pattern, content):
        full_match = match.group(0)
        fig_num = match.group(1)
        
        # Try to find the figure in metadata using different possible IDs
        fig_id = f"fig{fig_num}"
        
        if fig_id in figures_metadata:
            metadata = figures_metadata[fig_id]
            
            if metadata['type'] == 'figure':
                escaped_caption = escape_caption(metadata['caption'])
                escaped_caption = clean_latex(escaped_caption)
                replacement = f"""

{{{{< figure src="{fig_id}.png" caption="{escaped_caption}" >}}}}

Figure {fig_num}"""
            else:  # table
                table_caption = clean_latex(metadata['caption'])
                table_content = metadata['content']  # Don't clean LaTeX in table content
                replacement = f"""

**Table {fig_num}:** {table_caption}

{table_content}

"""
        else:
            logger.debug(f"Available figures in metadata: {list(figures_metadata.keys())}")
            logger.debug(f"Looking for figure {fig_id}")
            replacement = f'\n\n*[See Figure {fig_num} in the original paper]*\n\n'
        
        content = content.replace(full_match, replacement)
    
    # Clean up any multiple consecutive blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Ensure proper spacing between sections (numbered points)
    content = re.sub(r'(\d+\.) ', r'\n\n\1 ', content)
    
    return frontmatter + content

if __name__ == "__main__":
    main()
