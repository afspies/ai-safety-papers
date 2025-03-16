import logging
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Union, Any
from bs4 import BeautifulSoup
import re
import base64
from PIL import Image
from io import BytesIO
import time
from urllib.parse import urljoin
import json
import shutil

from backend.src.models.figure import Figure, FigureExtractor

logger = logging.getLogger(__name__)

class Ar5ivFigureExtractor(FigureExtractor):
    """Figure extractor using ar5iv HTML version of arXiv papers."""
    
    def __init__(self):
        self.logger = logger
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.current_base_url = None
    
    def extract_figures(self, source_path: Path, output_dir: Path) -> List[Figure]:
        """
        Extract figures from an ar5iv URL.
        
        Args:
            source_path: Path to a file containing the arXiv ID or URL
            output_dir: Directory to save extracted figures
            
        Returns:
            List of Figure objects
        """
        try:
            # Read arXiv ID or URL from file
            with open(source_path, 'r') as f:
                arxiv_id = f.read().strip()
            
            # Convert to ar5iv URL if it's an arXiv URL or ID
            ar5iv_url = self._get_ar5iv_url(arxiv_id)
            self.logger.info(f"Processing paper from ar5iv URL: {ar5iv_url}")
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Fetch HTML content
            response = self._fetch_with_retry(ar5iv_url)
            
            # Set base URL for resolving relative URLs
            paper_id = ar5iv_url.split('/')[-1]
            self.current_base_url = f"https://ar5iv.labs.arxiv.org/html/{paper_id}"
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract figures
            figures = []
            figure_elements = soup.find_all('figure')
            
            for idx, element in enumerate(figure_elements):
                # Skip subfigures - we'll process these with their parent
                if 'ltx_figure_panel' in element.get('class', []):
                    continue
                
                try:
                    # Get figure ID and element type
                    element_id = element.get('id', '')
                    
                    # Extract figure/table number from ID
                    id_match = re.search(r'[SF](\d+)\.([FT])(\d+)', element_id)
                    if id_match:
                        section_num, elem_type, elem_num = id_match.groups()
                        is_appendix = section_num.startswith('A')
                        elem_type = 'tab' if elem_type == 'T' else 'fig'
                        fig_id = f"{'appendix_' if is_appendix else ''}{elem_type}{elem_num}"
                    else:
                        # Fallback to simple numbering if ID doesn't match expected format
                        is_appendix = element_id and element_id.startswith('A')
                        fig_id = f"{'appendix_' if is_appendix else ''}fig{idx + 1}"
                    
                    # Check if this is a figure with subfigures
                    subfigures = element.find_all('figure', class_='ltx_figure_panel')
                    has_subfigures = len(subfigures) > 0
                    
                    # Get main caption
                    main_caption = None
                    for caption_elem in element.find_all('figcaption', class_='ltx_caption'):
                        # Skip captions that are inside subfigures
                        if not caption_elem.find_parent('figure', class_='ltx_figure_panel'):
                            main_caption = caption_elem
                            break
                    
                    caption_text = self._clean_latex_from_html(main_caption) if main_caption else ""
                    
                    if has_subfigures:
                        # Process subfigures
                        subfigures_data = []
                        for subfig_idx, subfig in enumerate(subfigures):
                            try:
                                # Get subfigure letter from ID
                                subfig_id = subfig.get('id', '')
                                match = re.search(r'\.sf(\d+)', subfig_id)
                                letter = chr(96 + int(match.group(1))) if match else chr(97 + subfig_idx)
                                
                                # Process subfigure image
                                subfig_path = output_dir / f"{fig_id}_{letter}.png"
                                success = self._process_and_save_image(subfig, subfig_path)
                                
                                if success:
                                    # Get subfigure caption
                                    subfig_caption = subfig.find('figcaption', class_='ltx_caption')
                                    subfig_caption_text = self._clean_latex_from_html(subfig_caption) if subfig_caption else f"({letter})"
                                    
                                    subfigures_data.append({
                                        'id': letter,
                                        'caption': subfig_caption_text
                                    })
                            except Exception as e:
                                self.logger.warning(f"Error processing subfigure {subfig_idx}: {e}")
                                continue
                        
                        # Create figure with subfigures
                        if subfigures_data:
                            figure = Figure(
                                id=fig_id,
                                caption=caption_text,
                                has_subfigures=True,
                                subfigures=subfigures_data,
                                type="figure",
                                path=output_dir / f"{fig_id}.png"  # Main figure path (placeholder)
                            )
                            figures.append(figure)
                    else:
                        # Process regular figure
                        fig_path = output_dir / f"{fig_id}.png"
                        success = self._process_and_save_image(element, fig_path)
                        
                        if success:
                            figure = Figure(
                                id=fig_id,
                                caption=caption_text,
                                has_subfigures=False,
                                type="figure",
                                path=fig_path
                            )
                            figures.append(figure)
                
                except Exception as e:
                    self.logger.warning(f"Error processing figure element {idx}: {e}")
                    continue
            
            return figures
            
        except Exception as e:
            self.logger.error(f"Error extracting figures: {e}")
            return []
    
    def _process_and_save_image(self, element: BeautifulSoup, output_path: Path) -> bool:
        """Process an image element and save it to the output path."""
        try:
            # Find image element
            img = element.find('img')
            if not img:
                self.logger.warning("No img element found")
                return False
            
            # Get image source
            src = img.get('src') or img.get('data-src')
            if not src:
                self.logger.warning("No image source found")
                return False
            
            # Handle different image source types
            if src.startswith('data:'):
                # Process base64 encoded image
                return self._save_base64_image(src, output_path)
            else:
                # Make relative URLs absolute
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(self.current_base_url, src)
                
                # Download and save image
                return self._download_and_save_image(src, output_path)
            
        except Exception as e:
            self.logger.warning(f"Error processing image: {e}")
            return False
    
    def _save_base64_image(self, base64_str: str, output_path: Path) -> bool:
        """Save a base64 encoded image to a file."""
        try:
            # Extract base64 data part
            if ',' in base64_str:
                base64_data = base64_str.split(',')[1]
            else:
                base64_data = base64_str
            
            # Decode and save
            img_data = base64.b64decode(base64_data)
            with open(output_path, 'wb') as f:
                f.write(img_data)
            
            return True
        except Exception as e:
            self.logger.warning(f"Error saving base64 image: {e}")
            return False
    
    def _download_and_save_image(self, url: str, output_path: Path) -> bool:
        """Download an image from a URL and save it."""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            self.logger.warning(f"Error downloading image from {url}: {e}")
            return False
    
    def _fetch_with_retry(self, url: str, max_retries: int = 3) -> requests.Response:
        """Fetch URL with retry logic."""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
    
    def _get_ar5iv_url(self, arxiv_url: str) -> str:
        """Convert arxiv URL or ID to ar5iv URL."""
        try:
            # Extract arxiv ID from URL or use directly if it's an ID
            if 'arxiv.org' in arxiv_url:
                # Handle different URL formats
                patterns = [
                    r'(?:arxiv.org/(?:abs|pdf)/)?([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)',  # Modern format
                    r'(?:arxiv.org/(?:abs|pdf)/)?([a-z\-]+(?:\.[A-Z]{2})?/[0-9]{7}(?:v[0-9]+)?)'  # Old format
                ]
                
                for pattern in patterns:
                    id_match = re.search(pattern, arxiv_url)
                    if id_match:
                        arxiv_id = id_match.group(1)
                        break
                else:
                    raise ValueError(f"Could not extract arXiv ID from URL: {arxiv_url}")
            else:
                arxiv_id = arxiv_url
            
            ar5iv_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
            return ar5iv_url
        
        except Exception as e:
            self.logger.error(f"Error converting URL: {arxiv_url}")
            raise
    
    def _clean_latex_from_html(self, element) -> str:
        """Extract and clean text from HTML elements, handling LaTeX math."""
        if not element:
            return ""
        
        # For NavigableString (plain text), just return the string
        if not hasattr(element, 'children'):
            return str(element)
            
        # Get text content
        text = ""
        for child in element.children:
            if hasattr(child, 'name'):
                if child.name == 'math':
                    # Handle math elements
                    latex = child.get('alttext', '')
                    if latex:
                        if not latex.startswith('$') and not latex.endswith('$'):
                            text += f" ${latex}$ "
                        else:
                            text += f" {latex} "
                    else:
                        text += child.get_text()
                else:
                    text += self._clean_latex_from_html(child)
            else:
                text += str(child)
        
        # Clean up spacing and formatting
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Extract caption without label
        label_match = re.match(r'^(Figure|Table)\s*(\d+):\s*(.+)$', text, re.IGNORECASE)
        if label_match:
            text = label_match.group(3).strip()
        
        # Extract subfigure caption without label
        subfig_match = re.match(r'^\(([a-z])\)\s*(.*)$', text, re.IGNORECASE)
        if subfig_match:
            letter, content = subfig_match.groups()
            text = content.strip() if content else f"({letter})"
        
        return text