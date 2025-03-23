#!/usr/bin/env python3
"""
Script to run the full AI Safety Papers processing pipeline with a real-world paper.
This script uses the Semantic Scholar API directly to get a paper
and processes it through our pipeline, storing data in Supabase and figures in Cloudflare R2.
"""

import os
import sys
from pathlib import Path
import logging
import json
import requests
import argparse
from datetime import datetime

WEBSITE_CONTENT_PATH = "processed_papers"

# Add the project root to Python path
project_root = Path(__file__).parent.parent
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

def main():
    parser = argparse.ArgumentParser(description='Run the AI Safety Papers processing pipeline')
    parser.add_argument('--paper-id', type=str, help='Process a specific paper by ID')
    parser.add_argument('--query', type=str, default='AI Safety', help='Search query for Semantic Scholar')
    parser.add_argument('--months', type=int, default=3, help='Months of papers to look back')
    parser.add_argument('--limit', type=int, default=1, help='Number of papers to process')
    parser.add_argument('--use-mock-supabase', action='store_true', help='Use mock Supabase for storage')
    parser.add_argument('--skip-figures', action='store_true', help='Skip figure extraction')
    parser.add_argument('--skip-summary', action='store_true', help='Skip summary generation')
    parser.add_argument('--skip-markdown', action='store_true', help='Skip markdown generation')
    parser.add_argument('--ignore-date-range', action='store_true', help='Ignore date range')
    args = parser.parse_args()

    # Always use development mode for now
    #os.environ['DEVELOPMENT_MODE'] = 'true'
    
    # Load configuration
    config = load_config()
    logger.info("Configuration loaded")
    
    # Initialize Supabase client
    try:
        db = SupabaseDB()
        logger.info("Supabase DB initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {e}")
        return

    # Create API clients - use development mode to avoid rate limiting
    semantic_scholar_api = SemanticScholarAPI(api_key=None, development_mode=False)
    logger.info("Semantic Scholar API initialized in development mode")
    
    # Initialize summarizer in development mode
    paper_summarizer = PaperSummarizer(db=db)
    
    # Get papers to process
    papers_to_process = []
    if args.paper_id:
        # Get paper by ID from Semantic Scholar
        logger.info(f"Fetching paper with ID: {args.paper_id}")
        paper = semantic_scholar_api.get_paper_by_id(args.paper_id)
        if paper:
            papers_to_process = [paper]
        else:
            logger.error(f"Paper with ID {args.paper_id} not found")
            return
    else:
        # Get papers from Semantic Scholar based on query
        logger.info(f"Searching for papers with query: {args.query}")
        papers = semantic_scholar_api.get_relevant_papers(
            query=args.query, 
            months=args.months,
            limit=args.limit,
            ignore_date_range=args.ignore_date_range
        )
        papers_to_process = papers
    
    if not papers_to_process:
        logger.error("No papers found to process")
        return
    
    logger.info(f"Found {len(papers_to_process)} papers to process")
    
    # Process each paper
    for paper in papers_to_process:
        paper_id = paper['paperId']
        logger.info(f"Processing paper: {paper['title']} (ID: {paper_id})")
        
        try:
            # Set data folder and website content path
            data_dir = Path(config.get('data_dir', 'data'))
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create Article object
            article = Article(
                uid=paper_id,
                title=paper.get('title', ''),
                url=paper.get('url', ''),
                authors=[author.get('name', '') for author in paper.get('authors', [])],
                abstract=paper.get('abstract', ''),
                venue=paper.get('venue', ''),
                submitted_date=paper.get('publicationDate', '').split('T')[0] if paper.get('publicationDate') else None,
                website_content_path=WEBSITE_CONTENT_PATH,
                data_folder = data_dir / paper_id
            )
            # Add TLDR if available
            if paper.get('tldr'):
                article.set_tldr(paper.get('tldr', {}).get('text', '') if isinstance(paper.get('tldr'), dict) else paper.get('tldr', ''))
            
            # Add paper to database
            entry = {
                'id': paper_id,
                'title': paper.get('title', ''),
                'authors': [author.get('name', '') for author in paper.get('authors', [])],
                'year': paper.get('year'),
                'abstract': paper.get('abstract', ''),
                'url': paper.get('url', ''),
                'venue': paper.get('venue', ''),
                'submitted_date': paper.get('publicationDate', '').split('T')[0] if paper.get('publicationDate') else None,
                'include_on_website': True,  # Mark for website inclusion
                'highlight': False,  # Not a highlight by default
                'tldr': paper.get('tldr', {}).get('text', '') if isinstance(paper.get('tldr'), dict) else paper.get('tldr', '')
            }
            
            db.add_paper(entry)
            logger.info(f"Added paper to database: {paper_id}")
            
            # Extract and process figures
            post = None
            if not args.skip_figures:
                logger.info("Extracting figures...")
                # Create a Post object to work with FigureExtractorManager
                post = Post(article)
                
                # Initialize FigureExtractorManager (without article parameter)
                figure_extractor = FigureExtractorManager()
                
                # Extract figures using the manager
                success = figure_extractor.extract_figures(post)
                
                if success and post.figures:
                    logger.info(f"Extracted {len(post.figures)} figures")
                    
                    # Process display figures
                    figure_extractor.process_post_figures(post)
                    
                    # If using Supabase, figures are already uploaded to R2 by extract_figures
                    # Check if any figures have R2 URLs
                    r2_count = sum(1 for fig in post.figures.values() if hasattr(fig, 'r2_url') and fig.r2_url)
                    if r2_count > 0:
                        logger.info(f"Successfully uploaded {r2_count} figures to R2")
                    else:
                        logger.warning("No figures were uploaded to R2")
                else:
                    logger.warning("No figures were extracted")
            
            # Generate summary
            if not args.skip_summary:
                logger.info("Generating summary...")
                if not post:
                    post = Post(article)
                
                # Call the summarize method
                try:
                    article.download_pdf()
                    summary_result = paper_summarizer.summarize(article)
                    
                    if isinstance(summary_result, tuple) and len(summary_result) >= 3:
                        # Handle tuple return (summary, display_figures, thumbnail_figure)
                        summary, display_figures, thumbnail_figure = summary_result
                        success = True
                    elif isinstance(summary_result, dict):
                        # Handle dictionary return
                        success = summary_result.get('success', False)
                        summary = summary_result.get('summary', '')
                        display_figures = summary_result.get('display_figures', [])
                        thumbnail_figure = summary_result.get('thumbnail_figure') or (display_figures[0] if display_figures else None)
                    else:
                        # If unexpected result, assume it's just the summary text
                        success = bool(summary_result)
                        summary = str(summary_result) if summary_result else ''
                        display_figures = list(post.figures.keys()) if post.figures else []
                        thumbnail_figure = display_figures[0] if display_figures else None
                    
                    if success and summary:
                        # Update the post object
                        post.summary = summary
                        post.display_figures = display_figures
                        post.thumbnail_figure = thumbnail_figure
                        
                        # Save summary to file
                        post.save_summary()
                        
                        logger.info(f"Summary generated with {len(display_figures)} display figures")
                        
                        # Store summary in Supabase
                        if not args.use_mock_supabase and isinstance(db, SupabaseDB):
                            db.add_summary(paper_id, summary, display_figures, thumbnail_figure)
                            logger.info("Saved summary to Supabase")
                    else:
                        logger.error("Failed to generate valid summary")
                except Exception as e:
                    logger.error(f"Error generating summary: {e}")
                    logger.exception("Summary generation error details:")
            
            # Generate markdown post
            if not args.skip_markdown:
                logger.info("Generating markdown post...")
                
                # Reuse the Post object or load it if available
                if not post:
                    # Try to load existing post
                    post = Post.load_from_article(article)
                    # If loading failed, create a new one
                    if not post:
                        post = Post(article)
                        # Check if we have summary from Supabase
                        if not args.use_mock_supabase and isinstance(db, SupabaseDB):
                            summary_data = db.get_summary(paper_id)
                            if summary_data:
                                post.summary = summary_data.get('summary', '')
                                post.display_figures = summary_data.get('display_figures', [])
                                post.thumbnail_figure = summary_data.get('thumbnail_figure') or (post.display_figures[0] if post.display_figures else None)
                                
                                # Get figures from Supabase if not already loaded
                                if not post.figures and post.display_figures:
                                    figures_data = db.get_paper_figures(paper_id)
                                    if figures_data:
                                        for fig_data in figures_data:
                                            figure = Figure(fig_data['figure_id'])
                                            figure.r2_url = fig_data['url']
                                            figure.caption = fig_data['caption']
                                            post.figures[fig_data['figure_id']] = figure
                
                # Prepare post directory
                post_dir = post.post_dir
                post_dir.mkdir(parents=True, exist_ok=True)
                
                try:
                    # If using Supabase, generate markdown with R2 URLs
                    if args.use_mock_supabase and isinstance(db, SupabaseDB) and post.display_figures:
                        # Get figure URLs from Supabase
                        figure_urls = {}
                        for fig_id in post.display_figures:
                            url = db.get_figure_info(paper_id, fig_id)['remote_path']
                            if url:
                                figure_urls[fig_id] = url
                            elif fig_id in post.figures and hasattr(post.figures[fig_id], 'r2_url') and post.figures[fig_id].r2_url:
                                figure_urls[fig_id] = post.figures[fig_id].r2_url
                        
                        # Generate the markdown with R2 URLs
                        if figure_urls:
                            # Import Figure class to handle subfigures correctly
                            from src.models.figure import Figure
                            
                            # Generate markdown using the Post data
                            index_path = generate_simple_markdown(article, post.summary, figure_urls, post_dir)
                            logger.info(f"Generated markdown post with Supabase/R2 URLs at {index_path}")
                            
                            # Set the thumbnail if available
                            if post.thumbnail_figure and post.thumbnail_figure in figure_urls:
                                # We'll download the thumbnail from R2 if available
                                try:
                                    import requests
                                    thumbnail_url = figure_urls[post.thumbnail_figure]
                                    thumbnail_path = post_dir / "thumbnail.png"
                                    
                                    response = requests.get(thumbnail_url, stream=True, timeout=30)
                                    if response.status_code == 200:
                                        with open(thumbnail_path, 'wb') as f:
                                            for chunk in response.iter_content(chunk_size=8192):
                                                f.write(chunk)
                                        logger.info(f"Downloaded thumbnail from R2: {thumbnail_path}")
                                except Exception as e:
                                    logger.error(f"Error downloading thumbnail from R2: {e}")
                        else:
                            logger.warning("No figure URLs found, generating markdown with local paths")
                            # Generate with local paths as fallback
                            index_path = generate_simple_markdown(article, post.summary, {}, post_dir)
                            logger.info(f"Generated markdown post with local paths at {index_path}")
                    else:
                        # Generate with local paths
                        index_path = generate_simple_markdown(article, post.summary, {}, post_dir)
                        logger.info(f"Generated markdown post with local paths at {index_path}")
                    
                    # Process display figures to copy to post directory
                    if post.display_figures:
                        post.process_display_figures()
                    
                    # Set thumbnail
                    if post.thumbnail_figure:
                        post.set_thumbnail()
                        
                except Exception as e:
                    logger.error(f"Error generating markdown post: {e}")
                    logger.exception("Markdown generation error details:")
            
            logger.info(f"Finished processing paper: {paper_id}")
            
        except Exception as e:
            logger.error(f"Error processing paper {paper_id}: {e}")
            logger.exception("Full traceback:")

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
    
    # Copy a thumbnail if available, or create a placeholder
    thumbnail_path = post_dir / "thumbnail.png"
    data_dir = Path(article.data_folder) if hasattr(article, 'data_folder') else None
    
    if data_dir and (data_dir / "thumbnail.png").exists():
        # Copy existing thumbnail
        try:
            import shutil
            shutil.copy(data_dir / "thumbnail.png", thumbnail_path)
        except Exception as e:
            logger.error(f"Error copying thumbnail: {e}")
    
    return index_path

# Mock Supabase class for development
class MockSupabaseDB:
    def __init__(self):
        logger.info("Initializing mock SupabaseDB for standalone script")
        self.papers = []  # In-memory storage for development
        self.highlighted_papers = []  # In-memory storage for highlighted papers
        self.summaries = {}  # In-memory storage for summaries
        self.figures = {}  # In-memory storage for figures
        
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
    
    def add_summary(self, paper_id, summary, display_figures, thumbnail_figure=None):
        # Add summary to in-memory storage
        self.summaries[paper_id] = {
            'summary': summary,
            'display_figures': display_figures,
            'thumbnail_figure': thumbnail_figure
        }
        logger.info(f"Added summary to mock DB: {paper_id}")
        return True
    
    def get_summary(self, paper_id):
        # Get summary from in-memory storage
        return self.summaries.get(paper_id)
    
    def add_figures_batch(self, paper_id, figures):
        # Add figures to in-memory storage
        if paper_id not in self.figures:
            self.figures[paper_id] = {}
        
        for fig in figures:
            self.figures[paper_id][fig['figure_id']] = {
                'caption': fig.get('caption', ''),
                'url': f"/mock/figures/{paper_id}/{fig['figure_id']}.png"
            }
        
        logger.info(f"Added {len(figures)} figures to mock DB: {paper_id}")
        return True
    
    def get_figure_url(self, paper_id, figure_id):
        # Get figure URL from in-memory storage
        if paper_id in self.figures and figure_id in self.figures[paper_id]:
            return self.figures[paper_id][figure_id]['url']
        return None
    
    def get_paper_figures(self, paper_id):
        # Get all figures for a paper
        if paper_id in self.figures:
            return [
                {
                    'figure_id': fig_id,
                    'caption': fig_data.get('caption', ''),
                    'url': fig_data.get('url', '')
                }
                for fig_id, fig_data in self.figures[paper_id].items()
            ]
        return []
        
if __name__ == "__main__":
    main()
