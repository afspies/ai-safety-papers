from pathlib import Path
from typing import Dict, List, Optional, Union
import shutil
import logging
from utils.figure_processor import extract_figures, create_thumbnail, load_or_parse_document
import requests
import os
from utils.ar5iv_figure_processor import Ar5ivFigureProcessor, FigureData, TableData

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
        self.tldr: Optional[str] = None
        self.raw_figures: List[Dict] = []  # Store raw figure data from processor
        
    def set_authors(self, authors: List[str]):
        """Set the authors list."""
        self.authors = authors
        
    def set_abstract(self, abstract: str):
        """Set the article abstract."""
        self.abstract = abstract
        
    def set_data_paths(self, data_dir: Path, pdf_path: Path):
        """Set the data directory and PDF path."""
        self.data_dir = data_dir
        self.data_folder = data_dir  # For backward compatibility
        self.pdf_path = pdf_path
        
    def process_figures(self) -> bool:
        """Process figures from PDF or HTML, including subfigures."""
        try:
            figures_dir = self.data_folder / "figures"
            figures_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize figure processor
            processor = Ar5ivFigureProcessor()
            
            # Process figures and get metadata
            elements = processor.process_paper(self.url, figures_dir)
            if not elements:
                logger.warning(f"No figures/tables found for article {self.uid}")
                return False
                
            # Store raw figure data for later use
            self.raw_figures = list(elements.values())
            
            # Update figures dictionary
            for elem_id, element_data in elements.items():
                if isinstance(element_data, FigureData):
                    if element_data.has_subfigures:
                        # Store main figure directory
                        self.figures[elem_id] = element_data.path
                        # Store individual subfigures
                        for subfig in element_data.subfigures:
                            subfig_id = f"{elem_id}_{subfig['id']}"  # e.g., fig1_a
                            self.figures[subfig_id] = Path(subfig['path'])
                    else:
                        self.figures[elem_id] = element_data.path
                elif isinstance(element_data, TableData):
                    # Handle tables
                    self.figures[elem_id] = element_data.path
            
            logger.info(f"Successfully processed {len(elements)} elements for article {self.uid}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing figures for article {self.uid}: {e}")
            logger.exception("Full traceback:")
            return False
        
    def set_displayed_figures(self, figure_ids: List[str]):
        """Set which figures should be displayed in the post."""
        self.displayed_figures = figure_ids
        
    def set_thumbnail_source(self, source: str):
        """
        Set the thumbnail source.
        
        Args:
            source: Either 'full', 'abstract', or a figure ID (e.g., 'fig1', 'fig1_a')
        """
        self.thumbnail_source = source
        
    def find_figure_by_label(self, label: str) -> Optional[str]:
        """
        Find a figure ID by its label (e.g., 'fig1', 'fig1_a').
        
        Args:
            label: The label to search for
            
        Returns:
            The full figure ID if found, None otherwise
        """
        # First try exact match
        if label in self.figures:
            return label
            
        # Then try suffix match for backward compatibility
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
        """Download the PDF from the article URL."""
        if not self.url or not self.pdf_path:
            logger.error("URL or PDF path not set")
            return False

        try:
            os.makedirs(self.pdf_path.parent, exist_ok=True)
            logger.debug(f"Downloading PDF from {self.url}")
            
            response = requests.get(self.url, stream=True)
            response.raise_for_status()

            if 'pdf' not in response.headers.get('content-type', '').lower():
                logger.error(f"URL does not point to a PDF (content-type: {response.headers.get('content-type')})")
                return False

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
            text = ""
            for page in self.parsed_doc.pages:
                text += page.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from document: {e}")
            return ""

    def set_tldr(self, tldr: str):
        """Set the TLDR summary."""
        self.tldr = tldr
