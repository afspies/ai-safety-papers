from typing import Dict, List, Optional, Any, Type
from pathlib import Path
import logging
import json
import re
import shutil

from src.models.article import Article
from src.models.figure import Figure 

logger = logging.getLogger(__name__)

class Post:
    """Class representing a blog post for a paper."""
    
    def __init__(
        self,
        article: Article,
        summary: str = "",
        figures: Dict[str, Figure] = None,
        display_figures: List[str] = None,
        thumbnail_figure: Optional[str] = None
    ):
        self.article = article
        self.summary = summary
        self.figures = figures or {}
        self.display_figures = display_figures or []
        self.thumbnail_figure = thumbnail_figure
        
    @property
    def post_dir(self) -> Path:
        """Get the directory path for the post."""
        content_path = Path(self.article.website_content_path) if hasattr(self.article, 'website_content_path') else None
        if not content_path:
            raise ValueError("Website content path not set for article")
            
        return content_path / "posts" / f"paper_{self.article.uid}"
        
    def get_figure(self, figure_id: str, download: bool = False) -> Optional[Figure]:
        """Get a figure by ID."""
        figure =  self.figures.get(figure_id)
        if figure and download:
            figure_id = figure.id
            local_fig_path = self.article.data_folder / "figures" / f"{figure_id}.png"
            if not local_fig_path.exists():
                # download figure from r2
                r2_path = figure.path
                if r2_path:
                    from src.utils.cloudflare_r2 import CloudflareR2Client
                    r2_client = CloudflareR2Client()
                    r2_client.download_file(r2_path, local_fig_path)
        return figure
        
    def extract_figures(self, extractor: "FigureExtractor", source_path: Path, force: bool = False) -> bool:
        """
        Extract figures using the provided extractor.

        Args:
            extractor: FigureExtractor implementation
            source_path: Path to the source file (pdf extraction) or arxiv url (ar5iv extraction)
            force: Whether to force extraction even if figures already exist
            
        Returns:
            True if extraction was successful
        """
        figures_dir = self.article.data_folder / "figures"
            
        # Create figures directory
        figures_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Extract figures
            extracted_figures = extractor.extract_figures(source_path, figures_dir)
            
            if not extracted_figures:
                logger.warning(f"No figures extracted from {source_path}")
                return False
                
            # Save metadata
            extractor.save_metadata(extracted_figures, figures_dir)
            
            # Update figures dictionary
            self.figures = {fig.id: fig for fig in extracted_figures}
            
            return True
        except Exception as e:
            logger.error(f"Error extracting figures: {e}")
            return False
    
    def process_display_figures(self) -> None:
        """Process display figures, preparing them for use in the post."""
        post_dir = self.post_dir
        post_dir.mkdir(parents=True, exist_ok=True)
        
        processed_main_figures = set()  # Track main figures we've processed
        
        for fig_id in self.display_figures:
            # Check if it's a subfigure reference (e.g., "2.a")
            subfig_match = re.match(r'(\d+)\.([a-z])', fig_id)
            if subfig_match:
                main_id = f"fig{subfig_match.group(1)}"
                subfig_id = subfig_match.group(2)
                
                # Get the main figure
                main_figure = self.get_figure(main_id)
                if not main_figure:
                    logger.warning(f"Main figure {main_id} not found for subfigure {fig_id}")
                    continue
                
                # Copy subfigure
                subfig_path = self.article.data_folder / "figures" / f"{main_id}_{subfig_id}.png"
                if subfig_path.exists():
                    shutil.copy2(subfig_path, post_dir / f"{main_id}_{subfig_id}.png")
                    
                # Also process the main figure if we haven't already
                if main_id not in processed_main_figures:
                    processed_main_figures.add(main_id)
                    figure = self.get_figure(main_id)
                    if figure and figure.path and "https:" not in str(figure.path):
                        if figure.path.exists():
                            figure.save_to_directory(post_dir)
                        else:
                            logger.warning(f"Figure {main_id} path does not exist")
            else:
                # Handle regular figure
                fig_id_clean = f"fig{fig_id}" if fig_id.isdigit() else fig_id
                figure = self.get_figure(fig_id_clean)
                
                if figure:
                    # Track that we've processed this main figure
                    processed_main_figures.add(fig_id_clean)
                    
                    if figure.path and "https:" not in str(figure.path):
                        # Check that figure exists
                        if figure.path.exists():
                            # Copy figure to post directory
                            figure.save_to_directory(post_dir)
                            
                            # If this figure has subfigures, process them too
                            if figure.has_subfigures:
                                for subfig in figure.subfigures:
                                    subfig_id = subfig.get('id')
                                    if subfig_id:
                                        subfig_path = self.article.data_folder / "figures" / f"{fig_id_clean}_{subfig_id}.png"
                                        if subfig_path.exists():
                                            shutil.copy2(subfig_path, post_dir / f"{fig_id_clean}_{subfig_id}.png")
                        else:
                            logger.warning(f"Figure {fig_id_clean} not found")
                else:
                    logger.warning(f"Figure {fig_id_clean} not found")

    def set_thumbnail(self) -> bool:
        """
        Set the thumbnail for the post.
        
        Returns:
            True if successful
        """
        post_dir = self.post_dir
        post_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.thumbnail_figure:
            # Use the first display figure if no thumbnail specified
            if self.display_figures:
                self.thumbnail_figure = self.display_figures[0]
            else:
                logger.warning("No thumbnail figure or display figures specified")
                return False
        
        # Check if it's a subfigure reference
        subfig_match = re.match(r'(\d+)\.([a-z])', self.thumbnail_figure)
        if subfig_match:
            main_id = f"fig{subfig_match.group(1)}"
            subfig_id = subfig_match.group(2)
            
            source_path = self.article.data_folder / "figures" / f"{main_id}_{subfig_id}.png"
            if source_path.exists():
                shutil.copy2(source_path, post_dir / "thumbnail.png")
                return True
        else:
            # Handle regular figure
            fig_id = f"fig{self.thumbnail_figure}" if self.thumbnail_figure.isdigit() else self.thumbnail_figure
            figure = self.get_figure(fig_id, download=True)
            
            if figure and figure.path:
                # Create a copy named thumbnail.png
                shutil.copy2(figure.path, post_dir / "thumbnail.png")
                return True
            else:
                source_path = self.article.data_folder / "figures" / f"{fig_id}.png"
                if source_path.exists():
                    shutil.copy2(source_path, post_dir / "thumbnail.png")
                    return True
                    
                # HANDLE EDGE CASE: Check if this is a main figure that has subfigures
                # but no main figure image
                if figure and figure.has_subfigures and figure.subfigures:
                    # Use the first subfigure as the thumbnail
                    first_subfig = figure.subfigures[0]
                    first_subfig_id = first_subfig.get('id')
                    if first_subfig_id:
                        subfig_path = self.article.data_folder / "figures" / f"{fig_id}_{first_subfig_id}.png"
                        if subfig_path.exists():
                            logger.info(f"Using first subfigure {fig_id}_{first_subfig_id} as thumbnail for {fig_id}")
                            shutil.copy2(subfig_path, post_dir / "thumbnail.png")
                            return True
                # If no subfigures found in the figure object, try to find subfigures in the figures directory
                subfig_pattern = f"{fig_id}_[a-z].png"
                subfig_files = list(self.article.data_folder.glob(f"figures/{subfig_pattern}"))
                if subfig_files:
                    # Use the first subfigure (alphabetically sorted)
                    subfig_files.sort()
                    logger.info(f"Found subfigures for {fig_id}, using {subfig_files[0].name} as thumbnail")
                    shutil.copy2(subfig_files[0], post_dir / "thumbnail.png")
                    return True
                    
        logger.warning(f"Thumbnail figure {self.thumbnail_figure} not found")
        return False
    
    def save_summary(self) -> Path:
        """
        Save the post summary to a JSON file.
        
        Returns:
            Path to the summary file
        """
        summary_path = self.article.data_folder / "summary.json"
        
        summary_data = {
            'summary': self.summary,
            'display_figures': self.display_figures,
            'thumbnail_figure': self.thumbnail_figure
        }
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=4, ensure_ascii=False)
            
        return summary_path
    
    @classmethod
    def load_from_article(cls, article: Article) -> Optional['Post']:
        """
        Load a post from an article, including summary and figures.
        
        Args:
            article: The article to load the post from
            
        Returns:
            Post instance or None if loading fails
        """
        # Load summary
        summary_path = article.data_folder / "summary.json"
        if not summary_path.exists():
            logger.warning(f"Summary not found for article {article.uid}")
            return None
            
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
                
            # Load figures
            figures_dir = article.data_folder / "figures"
            metadata_path = figures_dir / "figures_metadata.json"
            figures = FigureExtractor.load_metadata(metadata_path, figures_dir) if metadata_path.exists() else {}
            
            return cls(
                article=article,
                summary=summary_data.get('summary', ''),
                figures=figures,
                display_figures=summary_data.get('display_figures', []),
                thumbnail_figure=summary_data.get('thumbnail_figure')
            )
        except Exception as e:
            logger.error(f"Error loading post for article {article.uid}: {e}")
            return None