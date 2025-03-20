from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging
from pathlib import Path

from backend.src.models.article import Article
from backend.src.models.post import Post
from backend.src.models.supabase import SupabaseDB
from backend.src.api.schemas import PaperSummary, PaperDetail, FigureSchema

# Initialize router
router = APIRouter(tags=["papers"])
logger = logging.getLogger(__name__)

# Create a single instance of SupabaseDB to be shared across requests
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
                # Create PaperSummary
                base_url = f"/static/posts/paper_{article.uid}"
                summary = PaperSummary(
                    uid=article.uid,
                    title=article.title,
                    authors=article.authors,
                    abstract=article.abstract,
                    tldr=article.tldr,
                    thumbnail_url=f"{base_url}/thumbnail.png",
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
            # Create PaperSummary
            base_url = f"/static/posts/paper_{article.uid}"
            summary = PaperSummary(
                uid=article.uid,
                title=article.title,
                authors=article.authors,
                abstract=article.abstract,
                tldr=article.tldr,
                thumbnail_url=f"{base_url}/thumbnail.png",
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
            
        # Base URL for static assets
        base_url = f"/static/posts/paper_{article.uid}"
        
        # Create simplified response without figures for now
        return PaperDetail(
            uid=article.uid,
            title=article.title,
            authors=article.authors,
            abstract=article.abstract,
            tldr=article.tldr,
            summary=article.abstract,  # Use abstract as summary temporarily
            url=article.url,
            venue=article.venue,
            submitted_date=article.submitted_date,
            highlight=article.highlight,
            tags=getattr(article, 'tags', []),
            figures=[]  # Empty figures list for now
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))