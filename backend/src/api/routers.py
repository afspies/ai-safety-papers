from fastapi import APIRouter, HTTPException, Query, Depends, Body, Request
from fastapi.responses import RedirectResponse, JSONResponse
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
import os
import json

from src.models.supabase import SupabaseDB
from src.api.schemas import PaperSummary, PaperDetail, FigureSchema

# Initialize router
router = APIRouter(tags=["papers"])
logger = logging.getLogger(__name__)

# Create a single instance of SupabaseDB to be shared across requests
import os

# Check if in development mode
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
                
                # Make sure tags is always a list and never None
                article_tags = getattr(article, 'tags', [])
                if article_tags is None:
                    article_tags = []
                
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
                    tags=article_tags  # Use our safely processed tags
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
                
            # Make sure tags is always a list and never None
            article_tags = getattr(article, 'tags', [])
            if article_tags is None:
                article_tags = []
            
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
                tags=article_tags  # Use our safely processed tags
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
            from src.models.article import Article
            article_dict = article  # Rename for clarity
            article = Article(
                uid=article_dict['id'],
                title=article_dict['title'],
                url=article_dict['url'],
                authors=article_dict['authors'],
                abstract=article_dict.get('abstract', ''),
                venue=article_dict.get('venue', ''),
                submitted_date=article_dict.get('submitted_date'),
                appendix_page_number=article_dict.get('appendix_page_number')  # Make sure to include this
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
        raw_summary = ""  # Store the original summary
        markdown_summary = ""  # Default empty
        display_figures = []
        
        if summary_data:
            logger.info(f"Found summary for paper {paper_id}")
            raw_summary = summary_data['summary']  # Store the original summary with figure tags
            markdown_summary = summary_data.get('markdown_summary', '')
            display_figures = summary_data['display_figures']
            
            # If markdown_summary doesn't exist, generate it now
            if not markdown_summary and raw_summary:
                from src.summarizer.paper_summarizer import PaperSummarizer
                summarizer = PaperSummarizer(db=db)
                markdown_summary = summarizer.post_process_summary_to_markdown(paper_id, raw_summary)
                
                # Update the database with the generated markdown
                db.add_summary(
                    paper_id,
                    raw_summary,
                    display_figures,
                    summary_data.get('thumbnail_figure'),
                    markdown_summary
                )
            
            # Use markdown summary as the paper_summary (this is the key change)
            if markdown_summary:
                paper_summary = markdown_summary
            else:
                paper_summary = raw_summary
        
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
                
        # Make sure tags is always a list and never None
        article_tags = getattr(article, 'tags', [])
        if article_tags is None:
            article_tags = []
        
        # Create the response
        return PaperDetail(
            uid=article.uid,
            title=article.title,
            authors=article.authors,
            abstract=article.abstract,
            tldr=article.tldr,
            summary=paper_summary,  # This now contains the markdown summary
            raw_summary=raw_summary,  # Optionally keep the raw summary as a separate field
            markdown_summary=markdown_summary,  # Keep this field for backward compatibility
            url=article.url,
            venue=article.venue,
            submitted_date=article.submitted_date,
            highlight=article.highlight,
            tags=article_tags,
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
            from src.utils.config_loader import load_config
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
            