"""
Supabase database client and schema for AI Safety Papers.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from supabase import create_client, Client
from src.utils.cloudflare_r2 import CloudflareR2Client
from src.utils.config_loader import load_config
                
# Configure logging
logger = logging.getLogger(__name__)

class SupabaseDB:
    """Supabase database client for AI Safety Papers."""
    
    def __init__(self, url: str = None, key: str = None):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase URL
            key: Supabase API key
        """
        self.logger = logging.getLogger(__name__)
        
        # If no parameters are provided, attempt to load from config
        if not all([url, key]):
                
            config = load_config()
            url = os.environ.get("SUPABASE_URL") or config.get('supabase', {}).get('url')
            key = os.environ.get("SUPABASE_KEY") or config.get('supabase', {}).get('key')
            
        if not url or not key:
            raise ValueError("Supabase URL and API key are required")
            
        self.client = create_client(url, key)
        
            
        self.r2_client = CloudflareR2Client()
        self.logger.info("Initialized Supabase client and R2 client")
    
    def add_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new paper to the database.
        
        Args:
            paper: Paper data
            
        Returns:
            The added paper data
        """
        try:
            # Check if paper already exists
            existing = self.client.table('papers').select('id').eq('id', paper['id']).execute()
            if existing.data:
                self.logger.debug(f"Paper {paper['id']} already exists, updating instead")
                return self.update_paper(paper)
            
            # Insert paper
            result = self.client.table('papers').insert({
                'id': paper['id'],
                'title': paper.get('title', ''),
                'authors': paper.get('authors', []),
                'year': paper.get('year'),
                'abstract': paper.get('abstract', ''),
                'url': paper.get('url', ''),
                'venue': paper.get('venue', ''),
                'tldr': paper.get('tldr', {}).get('text', '') if isinstance(paper.get('tldr'), dict) else paper.get('tldr', ''),
                'submitted_date': paper.get('submitted_date'),
                'highlight': paper.get('highlight', False),
                'include_on_website': paper.get('include_on_website', False),
                'post_to_bots': paper.get('post_to_bots', False),
                'posted_date': paper.get('posted_date'),
                'ai_safety_relevance': paper.get('ai_safety_relevance', 0),
                'mech_int_relevance': paper.get('mech_int_relevance', 0),
                'embedding_model': paper.get('embedding_model', ''),
                'embedding_vector': paper.get('embedding_vector', []),
                'tags': paper.get('tags', [])
            }).execute()
            
            self.logger.debug(f"Added paper {paper['id']}")
            return result.data[0]
        except Exception as e:
            self.logger.error(f"Error adding paper {paper.get('id', 'unknown')}: {e}")
            raise
    
    def update_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing paper.
        
        Args:
            paper: Paper data with updated fields
            
        Returns:
            The updated paper data
        """
        try:
            # Update paper
            result = self.client.table('papers').update({
                'title': paper.get('title'),
                'authors': paper.get('authors'),
                'year': paper.get('year'),
                'abstract': paper.get('abstract'),
                'url': paper.get('url'),
                'venue': paper.get('venue'),
                'tldr': paper.get('tldr', {}).get('text', '') if isinstance(paper.get('tldr'), dict) else paper.get('tldr', ''),
                'highlight': paper.get('highlight'),
                'include_on_website': paper.get('include_on_website'),
                'post_to_bots': paper.get('post_to_bots'),
                'ai_safety_relevance': paper.get('ai_safety_relevance'),
                'mech_int_relevance': paper.get('mech_int_relevance'),
                'embedding_model': paper.get('embedding_model'),
                'embedding_vector': paper.get('embedding_vector'),
                'tags': paper.get('tags')
            }).eq('id', paper['id']).execute()
            
            self.logger.debug(f"Updated paper {paper['id']}")
            return result.data[0]
        except Exception as e:
            self.logger.error(f"Error updating paper {paper.get('id', 'unknown')}: {e}")
            raise
    
    def get_papers(self) -> List[Dict[str, Any]]:
        """
        Get all website-enabled papers.
        
        Returns:
            List of papers marked for website inclusion
        """
        try:
            from models.article import Article
            from utils.config_loader import load_config
            
            config = load_config()
            website_content_path = Path(config.get('website', {}).get('content_path', '../ai-safety-site/content/en'))
            data_dir = Path(config.get('data_dir', 'data'))
            
            # Get all papers that should be included on the website
            result = self.client.table('papers').select('*').eq('include_on_website', True).execute()
            
            papers = []
            for row in result.data:
                try:
                    article = Article(
                        uid=row['id'],
                        title=row['title'],
                        url=row['url'],
                        authors=row['authors'],
                        abstract=row['abstract'],
                        venue=row['venue'],
                        submitted_date=row['submitted_date']
                    )
                    
                    # Set TLDR
                    if row['tldr']:
                        article.set_tldr(row['tldr'])
                    
                    # Set highlight status
                    article.set_highlight(row.get('highlight', False))
                    
                    # Set website content path
                    article.website_content_path = website_content_path
                    
                    # Set data folder
                    data_path = data_dir / article.uid
                    article.data_folder = data_path
                    
                    # Set tags
                    article.tags = row.get('tags', [])
                    
                    papers.append(article)
                except Exception as row_e:
                    self.logger.error(f"Error processing row for paper {row.get('id', 'unknown')}: {row_e}")
                    continue
            
            self.logger.info(f"Successfully loaded {len(papers)} papers from Supabase")
            return papers
        except Exception as e:
            self.logger.error(f"Error getting papers: {e}")
            self.logger.exception("Full traceback:")
            return []
    
    def get_highlighted_papers(self) -> List[Dict[str, Any]]:
        """
        Get papers that are marked as highlights.
        
        Returns:
            List of highlighted papers
        """
        try:
            # Get highlighted papers directly from Supabase
            result = self.client.table('papers').select('*').eq('highlight', True).eq('include_on_website', True).execute()
            
            papers = []
            for row in result.data:
                try:
                    papers.append(self._row_to_article(row))
                except Exception as row_e:
                    self.logger.error(f"Error processing row for paper {row.get('id', 'unknown')}: {row_e}")
                    continue
            
            self.logger.info(f"Successfully loaded {len(papers)} highlighted papers from Supabase")
            return papers
        except Exception as e:
            self.logger.error(f"Error getting highlighted papers: {e}")
            self.logger.exception("Full traceback:")
            return []
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """
        Get a specific paper by its ID.
        
        Args:
            paper_id: Paper ID
            
        Returns:
            Paper data or None if not found
        """
        try:
            result = self.client.table('papers').select('*').eq('id', paper_id).execute()
            
            if not result.data:
                self.logger.warning(f"Paper {paper_id} not found")
                return None
            
            return self._row_to_article(result.data[0])
        except Exception as e:
            self.logger.error(f"Error getting paper by ID {paper_id}: {e}")
            return None
    
    def mark_as_posted(self, paper_id: str) -> bool:
        """
        Mark a paper as posted.
        
        Args:
            paper_id: Paper ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.table('papers').update({
                'posted_date': datetime.now().isoformat()
            }).eq('id', paper_id).execute()
            
            self.logger.debug(f"Marked paper {paper_id} as posted")
            return True
        except Exception as e:
            self.logger.error(f"Error marking paper {paper_id} as posted: {e}")
            return False
    
    def get_papers_to_post(self) -> List[Dict[str, Any]]:
        """
        Get papers that need to be posted.
        
        Returns:
            List of papers to post
        """
        try:
            # Get papers that need to be posted
            filter_condition = 'posted_date.is.null,highlight.eq.true'
            result = self.client.table('papers').select('*').or_(filter_condition).execute()
            
            papers_to_post = []
            for row in result.data:
                if (not row['posted_date'] and (row['post_to_bots'] or row['include_on_website'])) or \
                   (row['posted_date'] and row['highlight'] and row['include_on_website']):
                    papers_to_post.append(self._row_to_article(row))
            
            self.logger.info(f"Found {len(papers_to_post)} papers to post")
            return papers_to_post
        except Exception as e:
            self.logger.error(f"Error getting papers to post: {e}")
            return []
    
    def _row_to_article(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a database row to an article dict.
        
        Args:
            row: Database row
            
        Returns:
            Article dict
        """
        try:
            article = {
                'id': row['id'],
                'title': row['title'],
                'authors': row['authors'],
                'year': row['year'],
                'abstract': row['abstract'],
                'url': row['url'],
                'venue': row['venue'],
                'tldr': row['tldr'],
                'submitted_date': row['submitted_date'],
                'highlight': row['highlight'],
                'tags': row.get('tags', [])
            }
            return article
        except Exception as e:
            self.logger.error(f"Error converting row to article: {e}")
            return None
            
    # Summary management methods
    def add_summary(self, paper_id: str, summary: str, display_figures: List[str], thumbnail_figure: Optional[str] = None) -> bool:
        """
        Add or update a paper summary.
        
        Args:
            paper_id: Paper ID
            summary: Text summary
            display_figures: List of figure IDs to display
            thumbnail_figure: Optional thumbnail figure ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if summary already exists
            existing = self.client.table('paper_summaries').select('id').eq('id', paper_id).execute()
            
            if existing.data:
                # Update existing summary
                result = self.client.table('paper_summaries').update({
                    'summary': summary,
                    'display_figures': display_figures,
                    'thumbnail_figure': thumbnail_figure,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', paper_id).execute()
            else:
                # Insert new summary
                result = self.client.table('paper_summaries').insert({
                    'id': paper_id,
                    'summary': summary,
                    'display_figures': display_figures,
                    'thumbnail_figure': thumbnail_figure
                }).execute()
                
            self.logger.debug(f"Saved summary for paper {paper_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving summary for paper {paper_id}: {e}")
            return False
    
    def get_summary(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a paper summary.
        
        Args:
            paper_id: Paper ID
            
        Returns:
            Summary data if found, None otherwise
        """
        try:
            result = self.client.table('paper_summaries').select('*').eq('id', paper_id).execute()
            
            if not result.data:
                self.logger.warning(f"Summary for paper {paper_id} not found")
                return None
                
            return {
                'summary': result.data[0]['summary'],
                'display_figures': result.data[0]['display_figures'],
                'thumbnail_figure': result.data[0]['thumbnail_figure']
            }
        except Exception as e:
            self.logger.error(f"Error getting summary for paper {paper_id}: {e}")
            return None
            
    # Figure management methods with Cloudflare R2 integration
    def add_figure(self, paper_id: str, figure_id: str, image_data: bytes, caption: str = "", image_type: str = "image/png") -> bool:
        """
        Add or update a figure with Cloudflare R2 storage.
        
        Args:
            paper_id: Paper ID
            figure_id: Figure ID (e.g. "fig1", "fig2_a")
            image_data: Raw image data as bytes
            caption: Optional figure caption
            image_type: Image MIME type (default: image/png)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use the initialized R2 client
            # Create a key with paper_id and figure_id
            r2_key = f"figures/{paper_id}/{figure_id}.png"
            r2_url = self.r2_client.upload_file(image_data, r2_key, content_type=image_type)
            
            if not r2_url:
                self.logger.error(f"Failed to upload figure {figure_id} to R2")
                return False
                
            # Check if figure already exists in Supabase
            existing = self.client.table('paper_figures').select('id').eq('paper_id', paper_id).eq('figure_id', figure_id).execute()
            
            if existing.data:
                # Update existing figure
                result = self.client.table('paper_figures').update({
                    'caption': caption,
                    'r2_url': r2_url
                }).eq('paper_id', paper_id).eq('figure_id', figure_id).execute()
            else:
                # Insert new figure
                result = self.client.table('paper_figures').insert({
                    'paper_id': paper_id,
                    'figure_id': figure_id,
                    'caption': caption,
                    'r2_url': r2_url
                }).execute()
                
            self.logger.debug(f"Saved figure {figure_id} for paper {paper_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving figure {figure_id} for paper {paper_id}: {e}")
            return False
        
    def get_figure_info(self, paper_id: str, figure_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the figure information including R2 URL and local path.
        
        Args:
            paper_id: Paper ID
            figure_id: Figure ID
            
        Returns:
            Dict with 'remote_path', 'local_path', and 'caption' keys if found, None otherwise.
            Will attempt to upload from local storage if not found in R2.
        """
        try:
            # Get config for local path construction
            config = load_config()
            data_dir = Path(config.get('data_dir', 'data'))
            
            # Construct local path
            local_path = data_dir / paper_id / "figures" / f"{figure_id}.png"
            local_path_str = str(local_path)
            
            # Try Supabase first for remote path
            result = self.client.table('paper_figures').select('r2_url,caption').eq('paper_id', paper_id).eq('figure_id', figure_id).execute()
            
            if result.data and result.data[0]['r2_url']:
                return {
                    'remote_path': result.data[0]['r2_url'],
                    'local_path': local_path_str,
                    'caption': result.data[0].get('caption', ''),
                    'exists_locally': local_path.exists()
                }
                
            # Fall back to local storage only if it exists
            if local_path.exists():
                # Get captions if available
                caption = ""
                meta_path = data_dir / paper_id / "figures" / "figures.json"
                if meta_path.exists():
                    try:
                        with open(meta_path, 'r') as f:
                            figures_meta = json.load(f)
                            caption = figures_meta.get(figure_id, {}).get('caption', '')
                    except:
                        pass
                
                # Try to upload to R2 and get remote URL
                with open(local_path, 'rb') as f:
                    image_data = f.read()
                
                # Add to Supabase/R2
                self.add_figure(paper_id, figure_id, image_data, caption)
                
                # Try again to get the remote URL
                result = self.client.table('paper_figures').select('r2_url').eq('paper_id', paper_id).eq('figure_id', figure_id).execute()
                remote_path = result.data[0]['r2_url'] if result.data else None
                
                # Return both paths
                return {
                    'remote_path': remote_path,
                    'local_path': local_path_str,
                    'caption': caption,
                    'exists_locally': True
                }
                
            self.logger.warning(f"Figure {figure_id} for paper {paper_id} not found in Supabase/R2 or local storage")
            return None
        except Exception as e:
            self.logger.error(f"Error getting figure info for {figure_id} (paper {paper_id}): {e}")
            # Try local fallback
            try:
                config = load_config()
                data_dir = Path(config['data_dir'])
                
                fig_path = data_dir / paper_id / "figures" / f"{figure_id}.png"
                local_path_str = str(fig_path)
                
                if fig_path.exists():
                    # Return paths with only local path available
                    return {
                        'remote_path': None,
                        'local_path': local_path_str,
                        'caption': "",
                        'exists_locally': True
                    }
            except Exception as local_e:
                self.logger.error(f"Error getting figure from local storage: {local_e}")
            return None
            
    def get_paper_figures(self, paper_id: str) -> List[Dict[str, Any]]:
        """
        Get all figures for a paper.
        
        Args:
            paper_id: Paper ID
            
        Returns:
            List of figure data with remote URLs and paths
        """
        try:
            result = self.client.table('paper_figures').select('figure_id,caption,r2_url').eq('paper_id', paper_id).execute()
            
            config = load_config()
            data_dir = Path(config.get('data_dir', 'data'))
            
            figures = []
            for row in result.data:
                # Construct local path
                local_path = str(data_dir / paper_id / "figures" / f"{row['figure_id']}.png")
                
                figures.append({
                    'figure_id': row['figure_id'],
                    'caption': row['caption'],
                    'remote_path': row['r2_url'],
                    'local_path': local_path
                })
                
            self.logger.debug(f"Retrieved {len(figures)} figures for paper {paper_id}")
            return figures
        except Exception as e:
            self.logger.error(f"Error getting figures for paper {paper_id}: {e}")
            return []
            
    def add_figures_batch(self, paper_id: str, figures: List[Dict[str, Any]]) -> bool:
        """
        Batch upload multiple figures to R2 and store URLs in Supabase.
        
        Args:
            paper_id: Paper ID
            figures: List of figure data dicts with figure_id, image_data, caption, content_type
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use the initialized R2 client (no need to import or create a new one)
            
            # Track successful uploads
            supabase_batch = []
            
            for fig in figures:
                try:
                    # Upload to R2
                    fig_id = fig['figure_id']
                    image_data = fig['image_data']
                    caption = fig.get('caption', '')
                    content_type = fig.get('content_type', 'image/png')
                    
                    # Create R2 key
                    r2_key = f"figures/{paper_id}/{fig_id}.png"
                    
                    # Upload file
                    r2_url = self.r2_client.upload_file(image_data, r2_key, content_type)
                    
                    if r2_url:
                        # Add to batch for Supabase
                        supabase_batch.append({
                            'paper_id': paper_id,
                            'figure_id': fig_id,
                            'caption': caption,
                            'r2_url': r2_url
                        })
                except Exception as fig_e:
                    self.logger.error(f"Error processing figure {fig.get('figure_id', 'unknown')}: {fig_e}")
                    continue
            
            # Insert all successful uploads to Supabase
            if supabase_batch:
                result = self.client.table('paper_figures').upsert(supabase_batch).execute()
                self.logger.debug(f"Added {len(supabase_batch)} figures in batch for paper {paper_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error batch adding figures for paper {paper_id}: {e}")
            return False