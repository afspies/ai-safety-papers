import logging
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple, NamedTuple, List, Union
from bs4 import BeautifulSoup
import re
import base64
from PIL import Image
from io import BytesIO
import time
from urllib.parse import urljoin
import json
from dataclasses import dataclass
from bs4.element import Tag

@dataclass
class ElementData:
    """Base class for figure and table data"""
    path: Path
    caption: str
    type: str
    element_id: str  # Store the original ar5iv ID

@dataclass
class FigureData(ElementData):
    has_subfigures: bool = False
    subfigures: List[Dict[str, str]] = None

@dataclass
class TableData(ElementData):
    content: str = None  # Markdown content

class Ar5ivFigureProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.current_base_url = None

    def process_paper(self, arxiv_url: str, output_dir: Path) -> Dict[str, Union[FigureData, TableData]]:
        """Process all figures and tables from the paper."""
        try:
            arxiv_html_url = self._get_ar5iv_url(arxiv_url)
            self.logger.info(f"Processing paper from ar5iv URL: {arxiv_html_url}")

            output_dir.mkdir(parents=True, exist_ok=True)
            response = self._fetch_with_retry(arxiv_html_url)
            
            arxiv_id = arxiv_html_url.split('/')[-1]
            self.current_base_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = {}

            # Process all figures and tables
            for element in soup.find_all(['figure', 'table']):
                try:
                    result = self._process_element(element, len(elements), output_dir)
                    if result:
                        elem_id, elem_data = result
                        elements[elem_id] = elem_data
                except Exception as e:
                    self.logger.warning(f"Error processing element: {e}")
                    continue

            self._save_metadata(elements, output_dir)
            return elements

        except Exception as e:
            self.logger.error(f"Error processing paper: {e}")
            raise

    def _process_element(self, element: BeautifulSoup, num: int, output_dir: Path) -> Optional[Tuple[str, Union[FigureData, TableData]]]:
        """Process a figure or table element."""
        try:
            # Skip if this is a subfigure - we'll process these with their parent
            if 'ltx_figure_panel' in element.get('class', []):
                return None

            # Get element ID and type
            element_id = element.get('id', '')
            is_table = bool(element.name == 'table' or element.find('table'))
            
            # Extract figure/table number from ID (e.g., "S3.F2" -> "2", "A4.T1" -> "1")
            id_match = re.search(r'[SF](\d+)\.([FT])(\d+)', element_id)
            if id_match:
                section_num, elem_type, elem_num = id_match.groups()
                is_appendix = section_num.startswith('A')
                elem_type = 'tab' if elem_type == 'T' else 'fig'
                elem_id = f"{'appendix_' if is_appendix else ''}{elem_type}{elem_num}"
                self.logger.debug(f"Extracted element ID {elem_id} from HTML ID {element_id}")
            else:
                # Fallback to old numbering if ID doesn't match expected format
                is_appendix = element_id and element_id.startswith('A')
                elem_type = 'tab' if is_table else 'fig'
                elem_id = f"{'appendix_' if is_appendix else ''}{elem_type}{num}"
                self.logger.debug(f"Using fallback element ID {elem_id} for HTML ID {element_id}")

            if is_table:
                return self._process_table(element, elem_id, output_dir, element_id)

            # Check if this is a figure with subfigures
            subfigures = element.find_all('figure', class_='ltx_figure_panel')
            
            if subfigures:
                self.logger.info(f"Found figure with {len(subfigures)} subfigures")
                # Get main caption - look for the caption that's not inside a subfigure
                main_caption = None
                for caption in element.find_all('figcaption', class_='ltx_caption ltx_centering'):
                    # Skip captions that are inside subfigures
                    if not caption.find_parent('figure', class_='ltx_figure_panel'):
                        main_caption = caption
                        break
                
                # Extract caption text without formatting
                main_caption_text = self._clean_latex_from_html(main_caption) if main_caption else ""
                
                self.logger.debug(f"Extracted main caption: {main_caption_text}")
                
                # Process each subfigure
                subfigures_data = []
                for idx, subfig in enumerate(subfigures):
                    try:
                        # Get subfigure letter from ID
                        subfig_id = subfig.get('id', '')
                        self.logger.debug(f"Processing subfigure {idx+1}/{len(subfigures)} with ID: {subfig_id}")
                        
                        match = re.search(r'\.sf(\d+)$', subfig_id)
                        letter = chr(96 + int(match.group(1))) if match else chr(97 + len(subfigures_data))
                        
                        # Process subfigure using the helper method
                        subfig_path = output_dir / f"{elem_id}_{letter}.png"
                        self.logger.debug(f"Attempting to save subfigure to: {subfig_path}")
                        
                        subfig_data = self._process_figure_element(subfig, subfig_path)
                        
                        if subfig_data:
                            self.logger.info(f"Successfully processed subfigure {letter}")
                            subfigures_data.append({
                                'id': letter,
                                'path': subfig_path,
                                'caption': ""  # Raw caption without formatting
                            })
                        else:
                            self.logger.warning(f"Failed to process subfigure {letter}")
                    
                    except Exception as e:
                        self.logger.exception(f"Error processing subfigure {idx+1}: {e}")
                        continue

                if subfigures_data:
                    self.logger.info(f"Successfully processed {len(subfigures_data)} subfigures")
                    figure_data = FigureData(
                        path=output_dir / elem_id,
                        caption=main_caption_text,  # Raw caption without formatting
                        type='figure',
                        element_id=element_id,
                        has_subfigures=True,
                        subfigures=subfigures_data
                    )
                    return elem_id, figure_data
                else:
                    self.logger.warning("No subfigures were successfully processed")

            else:
                # Process as single figure using the same helper method
                figure_path = output_dir / f"{elem_id}.png"
                figure_data = self._process_figure_element(element, figure_path)
                
                if figure_data:
                    return elem_id, FigureData(
                        path=figure_path,
                        caption=figure_data['caption'],
                        type='figure',
                        element_id=element_id,
                        has_subfigures=False
                    )

        except Exception as e:
            self.logger.exception(f"Error processing element: {e}")
            return None

    def _process_table(self, element: BeautifulSoup, elem_id: str, output_dir: Path, original_id: str) -> Optional[Tuple[str, TableData]]:
        """Process a table element."""
        try:
            # Find the actual table element
            table = element if element.name == 'table' else element.find('table')
            if not table:
                return None

            # Get caption
            caption = element.find('figcaption', class_='ltx_caption ltx_centering')
            caption_text = self._clean_latex_from_html(caption) if caption else ""

            # Convert table to markdown
            table_md = self._table_to_markdown(table)
            if not table_md:
                return None

            # Save table markdown
            output_path = output_dir / f"{elem_id}.md"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(table_md)   

            table_data = TableData(
                path=output_path,
                caption=caption_text,
                type='table',
                element_id=original_id,
                content=table_md
            )

            return elem_id, table_data

        except Exception as e:
            self.logger.error(f"Error processing table: {e}")
            return None

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

    def _process_figure_image(self, figure_elem: BeautifulSoup) -> Optional[Image.Image]:
        """Extract image from figure element."""
        try:
            # First try SVG
            svg = figure_elem.find('svg')
            if svg:
                self.logger.debug("Found SVG element")
                return self._process_svg(svg)

            # Then try regular image
            img = figure_elem.find('img')
            if not img:
                self.logger.warning("No img element found in figure")
                return None
            
            src = img.get('src') or img.get('data-src')
            if not src:
                self.logger.warning("No src attribute found in img element")
                return None
            
            self.logger.debug(f"Original image src: {src}")
            
            # Make relative URLs absolute
            if not src.startswith(('http://', 'https://', 'data:')):
                # Extract arxiv ID from src path if possible
                arxiv_id_match = re.search(r'/html/([^/]+)/', src)
                if arxiv_id_match:
                    arxiv_id = arxiv_id_match.group(1)
                    self.current_base_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
                    self.logger.debug(f"Extracted arxiv ID: {arxiv_id}")
                
                src = urljoin(self.current_base_url, src)
                self.logger.debug(f"Converted to absolute URL: {src}")
            
            if src.startswith('data:'):
                self.logger.debug("Processing base64 encoded image")
                return self._decode_base64_image(src)
            else:
                return self._download_image(src)
            
        except Exception as e:
            self.logger.exception(f"Error processing figure image: {e}")
            return None

    def _table_to_markdown(self, table_elem: BeautifulSoup) -> Optional[str]:
        """Convert HTML table to markdown format."""
        try:
            rows = table_elem.find_all('tr')
            if not rows:
                return None

            markdown_rows = []
            
            # Process header row
            header_cells = rows[0].find_all(['th', 'td'])
            if not header_cells:
                return None
                
            # Process headers with LaTeX support
            header = [self._clean_latex_from_html(cell) for cell in header_cells]
            markdown_rows.append('| ' + ' | '.join(header) + ' |')
            markdown_rows.append('|' + '|'.join(['---' for _ in header]) + '|')
            
            # Process data rows with LaTeX support
            for row in rows[1:]:
                cells = row.find_all('td')
                row_data = [self._clean_latex_from_html(cell) for cell in cells]
                markdown_rows.append('| ' + ' | '.join(row_data) + ' |')
            
            # Add proper spacing for markdown table
            table_md = '\n'.join(markdown_rows)
            
            # Ensure table is preceded and followed by blank lines
            table_md = f"\n{table_md}\n"
            
            return table_md

        except Exception as e:
            self.logger.warning(f"Error converting table to markdown: {e}")
            return None

    def _save_metadata(self, elements: Dict[str, Union[FigureData, TableData]], output_dir: Path):
        """Save figure/table metadata to JSON file."""
        metadata = {}
        for elem_id, data in elements.items():
            try:
                # Convert paths to relative paths
                if isinstance(data.path, Path):
                    rel_path = data.path.relative_to(output_dir)
                else:
                    rel_path = str(data.path)  # Fallback if path is already a string

                meta_entry = {
                    'path': str(rel_path),
                    'caption': data.caption,
                    'type': data.type,
                    'element_id': data.element_id,
                }
                
                if data.type == 'table':
                    meta_entry['content'] = data.content
                elif data.has_subfigures and data.subfigures:
                    # Ensure subfigures are properly included
                    meta_entry['subfigures'] = [
                        {
                            'id': subfig['id'],
                            'path': str(Path(subfig['path']).relative_to(output_dir)),
                            'caption': subfig['caption']
                        }
                        for subfig in data.subfigures
                    ]
                    self.logger.debug(f"Added {len(data.subfigures)} subfigures to metadata for {elem_id}")
                    
                metadata[elem_id] = meta_entry
                
            except Exception as e:
                self.logger.error(f"Error processing metadata for element {elem_id}: {e}")
                continue
        
        try:
            with open(output_dir / 'figures_metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Successfully saved metadata with {len(metadata)} elements")
        except Exception as e:
            self.logger.error(f"Error saving metadata file: {e}")

    def _process_svg(self, svg_elem: BeautifulSoup) -> Optional[Image.Image]:
        """Convert SVG element to PIL Image using cairosvg."""
        try:
            # Get the SVG as a string
            svg_str = str(svg_elem)
            
            # Convert SVG to PNG using cairosvg
            png_data = cairosvg.svg2png(bytestring=svg_str.encode('utf-8'))
            
            # Convert to PIL Image
            return Image.open(BytesIO(png_data))
            
        except Exception as e:
            # If cairosvg fails, try a simpler SVG conversion
            try:
                self.logger.warning(f"Primary SVG conversion failed: {e}, trying fallback method")
                # Simplified SVG with only essential attributes
                simplified_svg = self._simplify_svg(svg_elem)
                png_data = cairosvg.svg2png(bytestring=simplified_svg.encode('utf-8'))
                return Image.open(BytesIO(png_data))
            except Exception as e2:
                self.logger.exception(f"Fallback SVG conversion also failed: {e2}")
                return None

    def _simplify_svg(self, svg_elem: BeautifulSoup) -> str:
        """Simplify SVG by keeping only essential attributes."""
        # Create a new SVG element with basic attributes
        width = svg_elem.get('width', '100')
        height = svg_elem.get('height', '100')
        simplified = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        
        # Extract and simplify path elements
        for path in svg_elem.find_all('path'):
            d = path.get('d', '')
            if d:
                simplified += f'<path d="{d}" fill="black"/>'
        
        simplified += '</svg>'
        return simplified

    def _decode_base64_image(self, base64_str: str) -> Optional[Image.Image]:
        """Decode a base64 encoded image."""
        try:
            base64_data = base64_str.split(',')[1]
            img_data = base64.b64decode(base64_data)
            return Image.open(BytesIO(img_data))
        except Exception as e:
            self.logger.exception(f"Error decoding base64 image")
            return None

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download an image from a URL."""
        try:
            self.logger.debug(f"Downloading image from {url}")
            # Make URL absolute if it's relative
            if not url.startswith(('http://', 'https://')):
                if not self.current_base_url:
                    raise ValueError("Base URL not set")
                url = urljoin(self.current_base_url, url)
                self.logger.debug(f"Converted to absolute URL: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            self.logger.exception(f"Error downloading image from {url}")
            return None

    def _table_to_image(self, table_elem: BeautifulSoup) -> Optional[Image.Image]:
        """Convert a table element to an image."""
        # This is a placeholder - would need to implement table rendering
        self.logger.debug("Table to image conversion not yet implemented")
        return None

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
                        self.logger.debug(f"Extracted arXiv ID: {arxiv_id} from URL: {arxiv_url}")
                        break
                else:
                    raise ValueError(f"Could not extract arXiv ID from URL: {arxiv_url}")
            else:
                arxiv_id = arxiv_url
                self.logger.debug(f"Using provided arXiv ID: {arxiv_id}")

            ar5iv_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
            self.logger.debug(f"Converted to ar5iv URL: {ar5iv_url}")
            return ar5iv_url

        except Exception as e:
            self.logger.exception(f"Error converting URL: {arxiv_url}")
            raise

    def _clean_latex_from_html(self, element: Tag) -> str:
        """Extract and clean LaTeX from HTML math elements."""
        if not element:
            return ""
        
        # Get raw text first
        text = ""
        for child in element.children:
            if isinstance(child, Tag):
                if child.name == 'math':
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
        
        # Clean up spacing around math delimiters
        text = re.sub(r'\s+\$', ' $', text)
        text = re.sub(r'\$\s+', '$ ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Format figure and table labels with proper spacing
        # Match main figure/table labels
        label_match = re.match(r'^(Figure|Table)\s*(\d+):\s*(.+)$', text, re.IGNORECASE)
        if label_match:
            label_type, number, content = label_match.groups()
            return content.strip()
        
        # Match subfigure labels (e.g., "(a)")
        subfig_match = re.match(r'^\(([a-z])\)\s*(.*)$', text, re.IGNORECASE)
        if subfig_match:
            letter, content = subfig_match.groups()
            return content.strip() if content else ""
        
        return text.strip()

    # Add new function to handle subfigures
    def process_subfigures(self, figure_element):
        """
        Process a figure element that contains subfigures.
        Returns a list of (subfigure_id, image_url, subcaption) tuples.
        """
        subfigures = []
        for subfig in figure_element.find_all('figure', class_='ltx_figure_panel'):
            subfig_id = subfig.get('id', '')
            img = subfig.find('img')
            if img:
                image_url = img.get('src', '')
                subcaption = subfig.find('figcaption')
                subcaption_text = subcaption.get_text() if subcaption else ''
                subfigures.append((subfig_id, image_url, subcaption_text))
        return subfigures

    # Modify process_figure to handle subfigures
    def process_figure(self, figure_element):
        """
        Enhanced figure processing to handle both regular figures and subfigures.
        """
        figure_id = figure_element.get('id', '')
        main_caption = figure_element.find('figcaption', class_='ltx_caption')
        main_caption_text = main_caption.get_text() if main_caption else ''
        
        # Check if this is a figure with subfigures
        has_subfigures = bool(figure_element.find_all('figure', class_='ltx_figure_panel'))
        
        if has_subfigures:
            subfigures = self.process_subfigures(figure_element)
            return {
                'id': figure_id,
                'caption': main_caption_text,
                'has_subfigures': True,
                'subfigures': subfigures
            }
        else:
            # Handle regular figure as before
            img = figure_element.find('img')
            if img:
                image_url = img.get('src', '')
                return {
                    'id': figure_id,
                    'image_url': image_url,
                    'caption': main_caption_text,
                    'has_subfigures': False
                }
        return None

    def _process_figure_element(self, figure_elem: BeautifulSoup, output_path: Path) -> Optional[Dict]:
        """Process any figure element (both single figures and subfigures)."""
        try:
            # Get figure ID and caption
            figure_id = figure_elem.get('id', '')
            caption = figure_elem.find('figcaption', class_='ltx_caption')
            caption_text = self._clean_latex_from_html(caption) if caption else ""
            
            # Process image
            img = self._process_figure_image(figure_elem)
            if not img:
                return None
            
            # Save image
            img.save(output_path, format='PNG')
            
            return {
                'id': figure_id,
                'path': output_path,
                'caption': caption_text
            }
            
        except Exception as e:
            self.logger.warning(f"Error processing figure element: {e}")
            return None