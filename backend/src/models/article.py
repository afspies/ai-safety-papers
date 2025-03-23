from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import shutil
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class Article:
    """Class representing a scientific article."""
    
    def __init__(
        self,
        uid: str,
        title: str,
        url: str,
        authors: List[str] = None,
        abstract: str = "",
        pdf_path: Optional[Path] = None,
        data_folder: Optional[Path] = None,
        website_content_path: Optional[Path] = None,
        venue: str = "",
        submitted_date: Optional[datetime] = None
    ):
        self.uid = uid
        self.title = title
        self.url = url
        self.authors = authors or []
        self.abstract = abstract
        self.pdf_path = pdf_path
        self.data_folder = data_folder
        self.website_content_path = website_content_path
        self.venue = venue
        self.submitted_date = submitted_date
        self.tldr = ""  # Optional TL;DR summary
        self.tags: List[str] = []  # Optional tags/keywords
        self.highlight = False  # Whether this paper is highlighted
        self.figures: Dict[str, Any] = {}  # Figures extracted from the paper
        self.display_figures: List[str] = []  # Figures to display in post
        self.thumbnail_source: str = "full"  # Source for thumbnail image
        
    def set_authors(self, authors: List[str]) -> None:
        """Set the paper authors."""
        self.authors = authors
        
    def set_abstract(self, abstract: str) -> None:
        """Set the paper abstract."""
        self.abstract = abstract
        
    def set_tldr(self, tldr: str) -> None:
        """Set the paper TLDR."""
        self.tldr = tldr
        
    def set_highlight(self, highlight: bool) -> None:
        """Set whether this paper is highlighted."""
        self.highlight = highlight
        
    def set_data_paths(self, data_folder: Path, pdf_path: Path) -> None:
        """Set the data folder and PDF path."""
        self.data_folder = data_folder
        self.pdf_path = pdf_path
    
    def set_displayed_figures(self, figures: List[str]) -> None:
        """Set which figures to display in the post."""
        self.display_figures = figures
    
    def set_thumbnail_source(self, source: str) -> None:
        """Set the source figure for the thumbnail."""
        self.thumbnail_source = source
    
    def download_pdf(self) -> bool:
        """Download the PDF for this article."""
        if not self.url or not self.data_folder:
            logger.error(f"Cannot download PDF: URL or data folder not set for {self.uid}")
            return False
            
        try:
            # Create data folder if it doesn't exist
            self.data_folder.mkdir(parents=True, exist_ok=True)
            
            # Set default PDF path if not set
            if not self.pdf_path:
                self.pdf_path = self.data_folder / "paper.pdf"
                
            # Skip if file already exists
            if self.pdf_path.exists():
                logger.debug(f"PDF already exists for {self.uid}")
                return True
                
            # If it's an arXiv URL, adapt for PDF download
            print("Downloading PDF for:")
            print(self.url)
            if 'arxiv.org' in self.url:
                parsed_url = urlparse(self.url)
                path_parts = parsed_url.path.strip('/').split('/')
                if len(path_parts) > 0:
                    arxiv_id = path_parts[-1]
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                else:
                    logger.error(f"Could not parse arXiv ID from URL: {self.url}")
                    return False
            else:
                logger.warning(f"Not an arXiv URL, using original URL for PDF: {self.url}")
                pdf_url = self.url
                
            # Download PDF
            response = requests.get(pdf_url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(self.pdf_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.debug(f"Downloaded PDF for {self.uid}")
                return True
            else:
                logger.error(f"Failed to download PDF for {self.uid}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading PDF for {self.uid}: {e}")
            return False
    
    def create_thumbnail(self) -> Optional[Path]:
        """Create a thumbnail for this article."""
        if not self.data_folder:
            logger.error(f"Cannot create thumbnail: data folder not set for {self.uid}")
            return None
            
        try:
            # Create figures directory if it doesn't exist
            figures_dir = self.data_folder / "figures"
            if not figures_dir.exists():
                logger.warning(f"Figures directory does not exist for {self.uid}")
                return None
                
            thumbnail_path = self.data_folder / "thumbnail.png"
            
            # Choose source based on thumbnail source setting
            if self.thumbnail_source == 'full':
                # Use the first figure as thumbnail
                for fig_path in figures_dir.glob("*.png"):
                    shutil.copy2(fig_path, thumbnail_path)
                    logger.debug(f"Created thumbnail for {self.uid} from {fig_path.name}")
                    return thumbnail_path
            else:
                # Use specific figure as thumbnail
                source_path = figures_dir / f"{self.thumbnail_source}.png"
                if source_path.exists():
                    shutil.copy2(source_path, thumbnail_path)
                    logger.debug(f"Created thumbnail for {self.uid} from {source_path.name}")
                    return thumbnail_path
                else:
                    logger.warning(f"Thumbnail source {self.thumbnail_source} not found for {self.uid}")
                    
            logger.warning(f"No suitable thumbnail source found for {self.uid}")
            return None
            
        except Exception as e:
            logger.error(f"Error creating thumbnail for {self.uid}: {e}")
            return None