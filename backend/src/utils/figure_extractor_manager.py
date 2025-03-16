import logging
from pathlib import Path
from typing import List, Optional, Dict, Type, Any
from backend.src.models.figure import Figure, FigureExtractor
from backend.src.models.post import Post
from backend.src.utils.ar5iv_figure_extractor import Ar5ivFigureExtractor
from backend.src.utils.pdf_figure_extractor import PdfFigureExtractor

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
        # Check if figures already exist in the post
        if post.figures and not force:
            self.logger.info(f"Figures already exist for post {post.article.uid}")
            return True
        
        # Try ar5iv extractor first
        figures_dir = post.article.data_folder / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        success = post.extract_figures(self.extractors[0], arxiv_id_path, force)
        
        # If ar5iv extractor fails, try PDF extractor
        if not success and pdf_path.exists():
            self.logger.info(f"Ar5iv extraction failed, trying PDF extraction")
            success = post.extract_figures(self.extractors[1], pdf_path, force)
        
        return success
    
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