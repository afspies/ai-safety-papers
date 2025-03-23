import logging
import json
from typing import List
from src.models.figure import Figure 
from src.models.post import Post
from .ar5iv_figure_extractor import Ar5ivFigureExtractor
from .pdf_figure_extractor import PdfFigureExtractor
from src.models.supabase import SupabaseDB

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
        
        # Initialize SupabaseDB once
        try:
            self.db = SupabaseDB()
        except Exception as e:
            self.logger.warning(f"Error initializing SupabaseDB: {e}")
            self.db = None
    
    def extract_figures(
        self, 
        post: Post, 
        force: bool = False
    ) -> bool:
        """
        Extract figures for a post using all available extractors.
        
        Args:
            post: Post object to add figures to
            force: Whether to force extraction even if figures already exist
            
        Returns:
            True if extraction was successful using any method
        """
        paper_id = post.article.uid
        
        # Check if figures already exist in Supabase/R2
        if not force and self.db is not None:
            try:
                figures = self.db.get_paper_figures(paper_id)
                if figures:
                    self.logger.info(f"Figures already exist in Supabase/R2 for paper {paper_id}")
                    # Add figures to post object
                    for fig_data in figures:
                        figure = Figure(fig_data['figure_id'])
                        figure.caption = fig_data['caption']
                        figure.remote_path = fig_data['remote_path']
                        figure.local_path = fig_data['local_path']
                        post.figures[fig_data['figure_id']] = figure
                    return True
            except Exception as e:
                self.logger.warning(f"Error checking Supabase for figures: {e}. Continuing with extraction.")
        
        # Check if figures already exist in the post
        if post.figures and not force:
            self.logger.info(f"Figures already exist for post {paper_id}")
            return True

        # Check if figures already exist for the post
        figures_dir = post.article.data_folder / "figures"
        metadata_path = figures_dir / "figures_metadata.json"
        if metadata_path.exists() and not force:
            logger.info(f"Figures already exist for {paper_id}. Loading metadata.")
            post.figures = self.extractors[0].load_metadata(metadata_path, figures_dir)
            return True
        
        # Try ar5iv extractor first
        figures_dir.mkdir(parents=True, exist_ok=True)
        success = post.extract_figures(self.extractors[0], post.article.url, force)
        
        # If ar5iv extractor fails, try PDF extractor
        pdf_path = post.article.pdf_path
        if pdf_path is None:
            self.logger.warning(f"No PDF path found for {paper_id}")
            return False
        if not success and pdf_path.exists():
            self.logger.info(f"Ar5iv extraction failed, trying PDF extraction")
            success = post.extract_figures(self.extractors[1], pdf_path, force)
        
        # If extraction was successful using local extractors, set the local path
        if success:
            figures_dir = post.article.data_folder / "figures"
            for fig_id, figure in post.figures.items():
                fig_path = figures_dir / f"{fig_id}.png"
                if fig_path.exists():
                    figure.local_path = str(fig_path)  # Set the local path
                    figure.remote_path = None  # No remote path yet
            
            # Try to store in R2
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
            
        # Skip if DB is not initialized
        if self.db is None:
            self.logger.warning("SupabaseDB not initialized, skipping R2 storage")
            return False
            
        try:
            paper_id = post.article.uid
            figures_dir = post.article.data_folder / "figures"
            
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
                result = self.db.add_figures_batch(paper_id, figures_batch)
                if result:
                    # Update figure objects with remote paths
                    figures = self.db.get_paper_figures(paper_id)
                    for fig_data in figures:
                        fig_id = fig_data['figure_id']
                        if fig_id in post.figures:
                            post.figures[fig_id].remote_path = fig_data['remote_path']
                
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
        # Set display figures if provided
        if requested_figures:
            post.display_figures = requested_figures
        
        # If no display figures are set, try to get all available figures
        if not post.display_figures and post.figures:
            post.display_figures = list(post.figures.keys())
        
        # Process display figures - ensure paths are properly set
        if post.display_figures:
            # Verify all figures have proper paths
            for fig_id in post.display_figures:
                if fig_id in post.figures:
                    figure = post.figures[fig_id]
                    # If missing paths, try to get them from the database
                    if not hasattr(figure, 'remote_path') or not hasattr(figure, 'local_path'):
                        if self.db:
                            fig_info = self.db.get_figure_info(post.article.uid, fig_id)
                            if fig_info:
                                figure.remote_path = fig_info['remote_path']
                                figure.local_path = fig_info['local_path']
                                figure.caption = fig_info.get('caption', '') or figure.caption
            
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
            