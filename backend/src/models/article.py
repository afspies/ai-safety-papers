from pathlib import Path
from typing import Dict, List, Optional
import shutil
import logging
from utils.figure_processor import extract_figures, create_thumbnail, load_or_parse_document
import requests
import os

logger = logging.getLogger(__name__)

class Article:
    def __init__(self, uid: str, title: str, url: str):
        self.uid = uid
        self.title = title
        self.url = url
        self.authors: List[str] = []
        self.figures: Dict[str, Path] = {}  # Maps figure IDs to their paths
        self.displayed_figures: List[str] = []  # List of figure IDs to display
        self.thumbnail_source: str = 'full'  # 'full', 'abstract', or a figure ID
        self.data_dir: Optional[Path] = None  # Directory for all article data
        self.pdf_path: Optional[Path] = None
        self.abstract: Optional[str] = None
        
    def set_authors(self, authors: List[str]):
        """Set the authors list."""
        self.authors = authors
        
    def set_abstract(self, abstract: str):
        """Set the article abstract."""
        self.abstract = abstract
        
    def set_data_paths(self, data_dir: Path, pdf_path: Path):
        """Set the data directory and PDF path."""
        self.data_dir = data_dir
        # For backward compatibility with code that uses data_folder
        self.data_folder = data_dir  
        self.pdf_path = pdf_path
        
    def process_figures(self) -> bool:
        """Extract figures from the PDF."""
        if not self.pdf_path or not self.data_dir:
            logger.error("PDF path or data directory not set")
            return False
            
        try:
            # Create figures directory
            figures_dir = self.data_dir / "figures"
            figures_dir.mkdir(parents=True, exist_ok=True)
            
            # Load document and store it
            doc, pdf_path = load_or_parse_document(self.pdf_path, self.data_dir)
            self.set_parsed_doc(doc)  # Set the parsed document
            
            # Extract figures
            self.figures = extract_figures(doc, figures_dir, pdf_path)
            logger.info(f"Extracted {len(self.figures)} figures")
            return True
            
        except Exception as e:
            logger.error(f"Error processing figures: {e}")
            return False
            
    def set_displayed_figures(self, figure_ids: List[str]):
        """Set which figures should be displayed in the post."""
        self.displayed_figures = figure_ids
        
    def set_thumbnail_source(self, source: str):
        """
        Set the thumbnail source.
        
        Args:
            source: Either 'full', 'abstract', or a figure ID (e.g., 'fig1')
        """
        self.thumbnail_source = source
        
    def find_figure_by_label(self, label: str) -> Optional[str]:
        """
        Find a figure ID by its label (e.g., 'fig1', 'tab2').
        
        Args:
            label: The label to search for
            
        Returns:
            The full figure ID if found, None otherwise
        """
        for fig_id in self.figures.keys():
            if fig_id.endswith(f"_{label}"):
                return fig_id
        return None
        
    def create_thumbnail(self) -> Optional[Path]:
        """Create thumbnail based on the specified source."""
        if not self.pdf_path or not self.data_dir:
            logger.error("PDF path or data directory not set")
            return None
            
        thumbnail_path = self.data_dir / "thumbnail.png"
        
        try:
            if self.thumbnail_source in ['full', 'abstract']:
                # Use the specified page mode
                doc, _ = load_or_parse_document(self.pdf_path, self.data_dir)
                return create_thumbnail(self.pdf_path, thumbnail_path, mode=self.thumbnail_source, doc=doc)
            else:
                # Try to find the specified figure
                figure_id = self.find_figure_by_label(self.thumbnail_source)
                if figure_id and figure_id in self.figures:
                    # Copy the figure to use as thumbnail
                    shutil.copy2(self.figures[figure_id], thumbnail_path)
                    return thumbnail_path
                else:
                    logger.warning(f"Specified thumbnail figure {self.thumbnail_source} not found, falling back to 'full' mode")
                    doc, _ = load_or_parse_document(self.pdf_path, self.data_dir)
                    return create_thumbnail(self.pdf_path, thumbnail_path, mode='full', doc=doc)
                    
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return None

    def download_pdf(self) -> bool:
        """
        Download the PDF from the article URL.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.url or not self.pdf_path:
            logger.error("URL or PDF path not set")
            return False

        try:
            # Create parent directory if it doesn't exist
            os.makedirs(self.pdf_path.parent, exist_ok=True)

            # Download the PDF
            logger.debug(f"Downloading PDF from {self.url}")
            response = requests.get(self.url, stream=True)
            response.raise_for_status()

            # Check if it's actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type:
                logger.error(f"URL does not point to a PDF (content-type: {content_type})")
                return False

            # Save the PDF
            with open(self.pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Successfully downloaded PDF to {self.pdf_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to download PDF: {e}")
            return False

    def set_parsed_doc(self, doc):
        """Set the parsed document."""
        self.parsed_doc = doc

    def get_raw_text(self) -> str:
        """Get the raw text from the parsed document."""
        if not hasattr(self, 'parsed_doc'):
            logger.error("No parsed document available")
            return ""
            
        try:
            # Extract text from all pages
            text = ""
            for page in self.parsed_doc.pages:
                text += page.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from document: {e}")
            return ""
