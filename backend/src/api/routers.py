from fastapi import APIRouter, HTTPException, Query, Depends, Body, Request
from fastapi.responses import RedirectResponse, JSONResponse
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
import os
import json

from backend.src.models.article import Article
from backend.src.models.post import Post
from backend.src.models.supabase import SupabaseDB
from backend.src.api.schemas import PaperSummary, PaperDetail, FigureSchema

# Initialize router
router = APIRouter(tags=["papers"])
logger = logging.getLogger(__name__)

# Create a single instance of SupabaseDB to be shared across requests
import os

# Check if in development mode
if os.environ.get('DEVELOPMENT_MODE') == 'true':
    # Create a mock SupabaseDB for development
    from backend.src.models.supabase import SupabaseDB
    from backend.src.models.article import Article
    
    class MockSupabaseDB(SupabaseDB):
        def __init__(self):
            logger.info("Initializing mock SupabaseDB for development")
            # Skip actual connection to Supabase
            self.papers = []  # In-memory storage for development
            self.highlighted_papers = []  # In-memory storage for highlighted papers
            self.logger = logging.getLogger(__name__)
            
        def get_papers(self):
            # Convert stored papers to Article objects
            return [self._paper_dict_to_article(paper) for paper in self.papers]
            
        def get_highlighted_papers(self):
            # Return highlighted papers
            return [self._paper_dict_to_article(paper) for paper in self.highlighted_papers]
            
        def get_paper_by_id(self, paper_id):
            # Find paper by ID
            for paper in self.papers:
                if paper.get('id') == paper_id:
                    return self._paper_dict_to_article(paper)
            return None
            
        def add_paper(self, paper_data):
            # Add paper to in-memory storage
            self.papers.append(paper_data)
            logger.info(f"Added paper to mock DB: {paper_data.get('id')}")
            return True
            
        def mark_as_posted(self, paper_id):
            # Mark paper as posted
            for paper in self.papers:
                if paper.get('id') == paper_id:
                    paper['posted'] = True
                    logger.info(f"Marked paper as posted: {paper_id}")
                    return True
            return False
            
        def get_papers_to_post(self):
            # Return papers that need to be posted (not yet posted)
            return [self._paper_dict_to_article(paper) for paper in self.papers if not paper.get('posted', False)]
            
        def mark_as_highlighted(self, paper_id, is_highlighted=True):
            # Mark paper as highlighted
            for paper in self.papers:
                if paper.get('id') == paper_id:
                    paper['highlight'] = is_highlighted
                    if is_highlighted:
                        # Add to highlighted papers if not already there
                        if paper not in self.highlighted_papers:
                            self.highlighted_papers.append(paper)
                    else:
                        # Remove from highlighted papers
                        self.highlighted_papers = [p for p in self.highlighted_papers if p.get('id') != paper_id]
                    logger.info(f"Marked paper highlight status as {is_highlighted}: {paper_id}")
                    return True
            return False
            
        def update_paper(self, paper_data):
            # Update existing paper
            for i, paper in enumerate(self.papers):
                if paper.get('id') == paper_data.get('id'):
                    self.papers[i] = paper_data
                    logger.info(f"Updated paper in mock DB: {paper_data.get('id')}")
                    return True
            # If not found, add it
            return self.add_paper(paper_data)
            
        def _paper_dict_to_article(self, paper_dict):
            # Convert a paper dictionary to an Article object
            if isinstance(paper_dict, Article):
                return paper_dict
                
            article = Article(
                uid=paper_dict.get('id'),
                title=paper_dict.get('title', ''),
                url=paper_dict.get('url', '')
            )
            
            # Set additional properties
            if paper_dict.get('authors'):
                article.set_authors(paper_dict['authors'])
            if paper_dict.get('abstract'):
                article.set_abstract(paper_dict['abstract'])
            if paper_dict.get('venue'):
                article.venue = paper_dict['venue']
            if paper_dict.get('submitted_date'):
                article.submitted_date = paper_dict['submitted_date']
            if paper_dict.get('tldr'):
                if isinstance(paper_dict['tldr'], dict):
                    article.set_tldr(paper_dict['tldr'].get('text', ''))
                else:
                    article.set_tldr(paper_dict['tldr'])
            if paper_dict.get('highlight'):
                article.set_highlight(paper_dict['highlight'])
            if paper_dict.get('tags'):
                article.tags = paper_dict['tags']
                
            return article
            
        # Add mock implementations for summary and figures
        def get_summary(self, paper_id):
            # Return a mock summary
            self.logger.info(f"Getting mock summary for paper {paper_id}")
            return {
                'summary': "This is a mock summary for testing purposes.",
                'display_figures': [],
                'thumbnail_figure': None
            }
            
        def get_paper_figures(self, paper_id):
            # Return empty figures list
            self.logger.info(f"Getting mock figures for paper {paper_id}")
            return []
            
        def get_figure_url(self, paper_id, figure_id):
            # Return a mock figure URL
            return f"/static/posts/paper_{paper_id}/thumbnail.png"
            
        def add_figure(self, paper_id, figure_id, image_data, caption="", image_type="image/png"):
            # Mock implementation - just log it
            self.logger.info(f"Mock adding figure {figure_id} for paper {paper_id}")
            return True
    
    supabase_db = MockSupabaseDB()
    logger.info("Created mock SupabaseDB instance for development mode")
else:
    supabase_db = SupabaseDB()
    logger.info("Created shared SupabaseDB instance")

def get_db():
    """Dependency to get the database connection."""
    return supabase_db


@router.get("/papers", response_model=List[PaperSummary])
async def get_papers(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: SupabaseDB = Depends(get_db)
):
    """
    Get a list of papers with basic information.
    
    Parameters:
    - limit: Maximum number of papers to return
    - offset: Number of papers to skip
    """
    try:
        # Get papers from Supabase
        logger.info("API: Getting papers from database")
        papers = db.get_papers()
        logger.info(f"API: Retrieved {len(papers)} papers from database")
        
        # Apply pagination
        paginated_papers = papers[offset:offset + limit]
        logger.info(f"API: After pagination: {len(paginated_papers)} papers")
        
        # Return empty list with custom message if no papers found
        if len(papers) == 0:
            logger.warning("API: No papers found in the database")
        
        # Convert to response format
        result = []
        for article in paginated_papers:
            try:
                # Check for thumbnail in Supabase
                thumbnail_url = f"/static/posts/paper_{article.uid}/thumbnail.png"  # Default
                
                try:
                    # Get summary to find thumbnail figure
                    summary_data = db.get_summary(article.uid)
                    if summary_data and summary_data.get('thumbnail_figure'):
                        # Try to get public URL for thumbnail
                        thumbnail_fig_id = summary_data['thumbnail_figure']
                        public_url = db.get_figure_url(article.uid, thumbnail_fig_id)
                        if public_url:
                            thumbnail_url = public_url
                except Exception as thumb_err:
                    logger.warning(f"Error getting thumbnail for {article.uid}: {thumb_err}")
                
                # Create PaperSummary
                summary = PaperSummary(
                    uid=article.uid,
                    title=article.title,
                    authors=article.authors,
                    abstract=article.abstract,
                    tldr=article.tldr,
                    thumbnail_url=thumbnail_url,
                    submitted_date=article.submitted_date,
                    highlight=article.highlight,
                    tags=getattr(article, 'tags', [])
                )
                result.append(summary)
            except Exception as article_error:
                logger.error(f"API: Error processing article {getattr(article, 'uid', 'unknown')}: {article_error}")
                # Continue processing other articles
        
        logger.info(f"API: Returning {len(result)} papers")
        return result
    except Exception as e:
        logger.error(f"API: Error getting papers: {e}")
        logger.exception("API: Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/highlighted", response_model=List[PaperSummary])
async def get_highlighted_papers(
    db: SupabaseDB = Depends(get_db)
):
    """
    Get all highlighted papers.
    """
    try:
        # Get highlighted papers from Supabase
        highlighted_papers = db.get_highlighted_papers()
        
        # Convert to response format
        result = []
        for article in highlighted_papers:
            # Check for thumbnail in Supabase
            thumbnail_url = f"/static/posts/paper_{article.uid}/thumbnail.png"  # Default
            
            try:
                # Get summary to find thumbnail figure
                summary_data = db.get_summary(article.uid)
                if summary_data and summary_data.get('thumbnail_figure'):
                    # Try to get public URL for thumbnail
                    thumbnail_fig_id = summary_data['thumbnail_figure']
                    public_url = db.get_figure_url(article.uid, thumbnail_fig_id)
                    if public_url:
                        thumbnail_url = public_url
            except Exception as thumb_err:
                logger.warning(f"Error getting thumbnail for {article.uid}: {thumb_err}")
                
            # Create PaperSummary
            summary = PaperSummary(
                uid=article.uid,
                title=article.title,
                authors=article.authors,
                abstract=article.abstract,
                tldr=article.tldr,
                thumbnail_url=thumbnail_url,
                submitted_date=article.submitted_date,
                highlight=article.highlight,
                tags=article.tags
            )
            result.append(summary)
            
        return result
    except Exception as e:
        logger.error(f"Error getting highlighted papers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{paper_id}", response_model=PaperDetail)
async def get_paper_detail(
    paper_id: str,
    db: SupabaseDB = Depends(get_db)
):
    """
    Get detailed information for a specific paper.
    
    Parameters:
    - paper_id: The unique identifier for the paper
    """
    try:
        # Get paper from Supabase
        article = db.get_paper_by_id(paper_id)
        
        if not article:
            raise HTTPException(status_code=404, detail=f"Paper with ID {paper_id} not found")
            
        # Handle both Article and dict responses from get_paper_by_id
        if not hasattr(article, 'uid'):
            # If we got a dictionary, convert it to an Article
            from backend.src.models.article import Article
            article_dict = article  # Rename for clarity
            article = Article(
                uid=article_dict['id'],
                title=article_dict['title'],
                url=article_dict['url'],
                authors=article_dict['authors'],
                abstract=article_dict.get('abstract', ''),
                venue=article_dict.get('venue', ''),
                submitted_date=article_dict.get('submitted_date')
            )
            if article_dict.get('tldr'):
                if isinstance(article_dict['tldr'], dict):
                    article.set_tldr(article_dict['tldr'].get('text', ''))
                else:
                    article.set_tldr(article_dict['tldr'])
            
            article.set_highlight(article_dict.get('highlight', False))
        
        # Get summary from Supabase
        summary_data = db.get_summary(paper_id)
        paper_summary = article.abstract
        display_figures = []
        
        if summary_data:
            logger.info(f"Found summary for paper {paper_id}")
            paper_summary = summary_data['summary']
            display_figures = summary_data['display_figures']
        
        # Get figures from Supabase
        figures_data = db.get_paper_figures(paper_id)
        
        figures = []
        for fig_data in figures_data:
            # Only include figures that are in the display_figures list (if we have one)
            if not display_figures or fig_data['figure_id'] in display_figures:
                figures.append(FigureSchema(
                    id=fig_data['figure_id'],
                    caption=fig_data['caption'],
                    url=fig_data['url'],
                    has_subfigures=False  # Default
                ))
                
        # Create the response
        return PaperDetail(
            uid=article.uid,
            title=article.title,
            authors=article.authors,
            abstract=article.abstract,
            tldr=article.tldr,
            summary=paper_summary,
            url=article.url,
            venue=article.venue,
            submitted_date=article.submitted_date,
            highlight=article.highlight,
            tags=getattr(article, 'tags', []),
            figures=figures
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add direct figure endpoints
@router.get("/papers/{paper_id}/figures/{figure_id}")
async def get_figure(paper_id: str, figure_id: str, db: SupabaseDB = Depends(get_db)):
    """
    Get a specific figure for a paper by redirecting to its R2 URL.
    
    Parameters:
    - paper_id: The unique identifier for the paper
    - figure_id: The figure identifier
    """
    try:
        # Get public figure URL from Supabase/R2
        public_url = db.get_figure_url(paper_id, figure_id)
        
        if not public_url:
            # Try to fall back to local storage if needed
            from backend.src.utils.config_loader import load_config
            config = load_config()
            data_dir = Path(config['data_dir'])
            
            fig_path = data_dir / paper_id / "figures" / f"{figure_id}.png"
            
            if fig_path.exists():
                # If local file exists but no R2 URL, we need to upload it
                with open(fig_path, 'rb') as f:
                    image_data = f.read()
                
                # Get caption if available
                caption = ""
                meta_path = data_dir / paper_id / "figures" / "figures.json"
                if meta_path.exists():
                    try:
                        with open(meta_path, 'r') as f:
                            figures_meta = json.load(f)
                            caption = figures_meta.get(figure_id, {}).get('caption', '')
                    except:
                        pass
                
                # Add to R2/Supabase
                db.add_figure(paper_id, figure_id, image_data, caption)
                
                # Try again to get the URL
                public_url = db.get_figure_url(paper_id, figure_id)
                
                if not public_url:
                    raise HTTPException(status_code=500, detail="Failed to create public URL")
            else:
                raise HTTPException(status_code=404, detail="Figure not found")
        
        # Redirect to the public URL
        return RedirectResponse(url=public_url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting figure {figure_id} for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/papers/{paper_id}/figures")
async def get_paper_figures(paper_id: str, db: SupabaseDB = Depends(get_db)):
    """
    Get all figures for a paper.
    
    Parameters:
    - paper_id: The unique identifier for the paper
    """
    try:
        figures = db.get_paper_figures(paper_id)
        return figures
    except Exception as e:
        logger.error(f"Error getting figures for paper {paper_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add a development-only endpoint to populate test data
if os.environ.get('DEVELOPMENT_MODE') == 'true':
    @router.post("/dev/add-test-papers")
    async def add_test_papers(db: SupabaseDB = Depends(get_db)):
        """
        Development-only endpoint to add test papers to the database.
        Only available when DEVELOPMENT_MODE=true.
        """
        try:
            # Sample papers for testing
            sample_papers = [
                {
                    'id': 'sample-paper-1',
                    'title': 'AI Safety: Test Paper 1',
                    'authors': ['John Doe', 'Jane Smith'],
                    'abstract': 'This is a test paper about AI safety.',
                    'url': 'https://example.com/paper1',
                    'venue': 'AI Safety Conference 2025',
                    'submitted_date': '2025-01-01',
                    'tldr': 'A brief summary of test paper 1.',
                    'highlight': True,
                    'tags': ['ai-safety', 'test'],
                    'posted': True
                },
                {
                    'id': 'sample-paper-2',
                    'title': 'AI Safety: Test Paper 2',
                    'authors': ['Bob Johnson', 'Alice Brown'],
                    'abstract': 'Another test paper about AI safety.',
                    'url': 'https://example.com/paper2',
                    'venue': 'AI Safety Conference 2025',
                    'submitted_date': '2025-02-01',
                    'tldr': 'A brief summary of test paper 2.',
                    'highlight': False,
                    'tags': ['ai-safety', 'test'],
                    'posted': True
                }
            ]
            
            # Add papers to database
            added_count = 0
            for paper in sample_papers:
                if db.add_paper(paper):
                    added_count += 1
            
            # Mark the first paper as highlighted
            db.mark_as_highlighted('sample-paper-1', True)
            
            return {"message": f"Added {added_count} test papers to database"}
        except Exception as e:
            logger.error(f"Error adding test papers: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    @router.post("/dev/add-custom-paper")
    async def add_custom_paper(paper: Dict[str, Any] = Body(...), db: SupabaseDB = Depends(get_db)):
        """
        Development-only endpoint to add a custom paper to the database.
        Only available when DEVELOPMENT_MODE=true.
        """
        try:
            # Add paper to database
            if db.add_paper(paper):
                # Mark as highlighted if needed
                if paper.get('highlight'):
                    db.mark_as_highlighted(paper['id'], True)
                return {"message": f"Added custom paper {paper.get('id', 'unknown')} to database"}
            else:
                raise HTTPException(status_code=500, detail="Failed to add paper to database")
        except Exception as e:
            logger.error(f"Error adding custom paper: {e}")
            raise HTTPException(status_code=500, detail=str(e))