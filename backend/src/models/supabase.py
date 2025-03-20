"""
Supabase database client and schema for AI Safety Papers.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from supabase import create_client, Client

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
            from utils.config_loader import load_config
            config = load_config()
            url = os.environ.get("SUPABASE_URL") or config.get('supabase', {}).get('url')
            key = os.environ.get("SUPABASE_KEY") or config.get('supabase', {}).get('key')
            
        if not url or not key:
            raise ValueError("Supabase URL and API key are required")
            
        self.client = create_client(url, key)
        self.logger.info("Initialized Supabase client")
    
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