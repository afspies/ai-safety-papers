import logging
import json
from pathlib import Path
from typing import List, Optional, Dict, Type, Any
from backend.src.models.figure import Figure, FigureExtractor
from backend.src.models.post import Post
from backend.src.utils.ar5iv_figure_extractor import Ar5ivFigureExtractor
from backend.src.utils.pdf_figure_extractor import PdfFigureExtractor
from backend.src.utils.cloudflare_r2 import CloudflareR2Client
from backend.src.models.supabase import SupabaseDB

logger = logging.getLogger(__name__)

class FigureExtractorManager:
    """
    Manager class that handles multiple figure extractors with fallback.
    Will try extraction methods in order until one succeeds or all fail.
    """
    
    def __init__(self):
        self.logger = logger
        self.extractors = [
            Ar5ivFigureExtractor(),  # Try ar5iv first
            PdfFigureExtractor()     # Fallback to PDF extraction
        ]
    
    def extract_figures(
        self, 
        post: Post, 
        arxiv_id_path: Path, 
        pdf_path: Path,
        force: bool = False
    ) -> bool:
        """
        Extract figures for a post using all available extractors.
        
        Args:
            post: Post object to add figures to
            arxiv_id_path: Path to a file containing the arXiv ID
            pdf_path: Path to the PDF file
            force: Whether to force extraction even if figures already exist
            
        Returns:
            True if extraction was successful using any method
        """
        paper_id = post.article.uid
        
        # Check if figures already exist in Supabase/R2
        if not force:
            try:
                db = SupabaseDB()
                figures = db.get_paper_figures(paper_id)
                if figures:
                    self.logger.info(f"Figures already exist in Supabase/R2 for paper {paper_id}")
                    # Add figures to post object
                    for fig_data in figures:
                        figure = Figure(fig_data['figure_id'])
                        figure.r2_url = fig_data['url']
                        figure.caption = fig_data['caption']
                        post.figures[fig_data['figure_id']] = figure
                    return True
            except Exception as e:
                self.logger.warning(f"Error checking Supabase for figures: {e}. Continuing with extraction.")
        
        # Check if figures already exist in the post
        if post.figures and not force:
            self.logger.info(f"Figures already exist for post {paper_id}")
            return True
        
        # Try ar5iv extractor first
        figures_dir = post.article.data_folder / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        success = post.extract_figures(self.extractors[0], arxiv_id_path, force)
        
        # If ar5iv extractor fails, try PDF extractor
        if not success and pdf_path.exists():
            self.logger.info(f"Ar5iv extraction failed, trying PDF extraction")
            success = post.extract_figures(self.extractors[1], pdf_path, force)
        
        # If extraction was successful, upload figures to R2 and store in Supabase
        if success:
            try:
                self.store_figures_in_r2(post)
            except Exception as e:
                self.logger.error(f"Error storing figures in R2: {e}")
                # Continue anyway - local storage will be used as fallback
        
        return success
        
    def store_figures_in_r2(self, post: Post) -> bool:
        """
        Store extracted figures in Cloudflare R2 via Supabase.
        
        Args:
            post: Post object with extracted figures
            
        Returns:
            True if storage was successful
        """
        if not post.figures:
            self.logger.warning("No figures to store in R2")
            return False
            
        try:
            paper_id = post.article.uid
            figures_dir = post.article.data_folder / "figures"
            db = SupabaseDB()
            
            # Load figure metadata if available
            figures_meta = {}
            meta_path = figures_dir / "figures.json"
            if meta_path.exists():
                try:
                    with open(meta_path, 'r') as f:
                        figures_meta = json.load(f)
                except Exception as meta_e:
                    self.logger.warning(f"Error loading figures metadata: {meta_e}")
            
            # Prepare batch of figures for upload
            figures_batch = []
            
            for fig_id, figure in post.figures.items():
                fig_path = figures_dir / f"{fig_id}.png"
                if fig_path.exists():
                    try:
                        with open(fig_path, 'rb') as f:
                            image_data = f.read()
                            
                        # Get caption from metadata or figure object
                        caption = figures_meta.get(fig_id, {}).get('caption', '') or figure.caption or ''
                        
                        figures_batch.append({
                            'figure_id': fig_id,
                            'image_data': image_data,
                            'caption': caption,
                            'content_type': 'image/png'
                        })
                    except Exception as fig_e:
                        self.logger.error(f"Error reading figure {fig_id}: {fig_e}")
            
            # Upload figures in batch
            if figures_batch:
                result = db.add_figures_batch(paper_id, figures_batch)
                self.logger.info(f"Stored {len(figures_batch)} figures in R2/Supabase for paper {paper_id}")
                return result
            else:
                self.logger.warning(f"No figures to upload for paper {paper_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error storing figures in R2/Supabase: {e}")
            return False
    
    def process_post_figures(
        self,
        post: Post,
        requested_figures: List[str] = None
    ) -> bool:
        """
        Process figures for a post, preparing them for display.
        
        Args:
            post: Post object to process figures for
            requested_figures: List of specific figure IDs to process
                (if None, will use post.display_figures)
            
        Returns:
            True if processing was successful
        """
        try:
            # Set display figures if provided
            if requested_figures:
                post.display_figures = requested_figures
            
            # If no display figures are set, try to get all available figures
            if not post.display_figures and post.figures:
                post.display_figures = list(post.figures.keys())
            
            # Process display figures
            if post.display_figures:
                post.process_display_figures()
                
                # Set thumbnail if not already set
                if not post.thumbnail_figure and post.display_figures:
                    post.thumbnail_figure = post.display_figures[0]
                
                # Process thumbnail
                post.set_thumbnail()
                
                return True
            else:
                self.logger.warning("No display figures to process")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing post figures: {e}")
            return False