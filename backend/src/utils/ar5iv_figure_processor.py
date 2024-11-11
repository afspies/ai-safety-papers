import logging
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple, NamedTuple
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
class FigureData:
    path: Path
    caption: str
    type: str  # 'figure' or 'table'
    content: Optional[str] = None  # For tables, stores markdown content

class Ar5ivFigureProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.current_base_url = None

    def process_paper(self, arxiv_url: str, output_dir: Path) -> Dict[str, FigureData]:
        """Extract figures and tables from an ar5iv HTML version of a paper."""
        try:
            arxiv_html_url = self._get_ar5iv_url(arxiv_url)
            self.logger.info(f"Processing paper from ar5iv URL: {arxiv_html_url}")

            output_dir.mkdir(parents=True, exist_ok=True)

            # Fetch and parse HTML
            response = self._fetch_with_retry(arxiv_html_url)
            
            # Set base URL for image downloads - ar5iv uses a specific structure
            arxiv_id = arxiv_html_url.split('/')[-1]
            self.current_base_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
            self.logger.debug(f"Set base URL to: {self.current_base_url}")

            soup = BeautifulSoup(response.text, 'html.parser')
            figures = {}
            
            # Process all figures and tables
            for fig_num, element in enumerate(soup.find_all(['figure', 'table'])):
                try:
                    result = self._process_element(element, fig_num, output_dir)
                    if result:
                        fig_id, figure_data = result
                        figures[fig_id] = figure_data
                except Exception as e:
                    self.logger.warning(f"Error processing element {fig_num}: {e}")
                    continue

            # Save metadata
            self._save_metadata(figures, output_dir)
            
            self.logger.info(f"Successfully extracted {len(figures)} elements")
            return figures

        except Exception as e:
            self.logger.error(f"Error processing paper: {e}")
            raise

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

    def _process_element(self, element: BeautifulSoup, num: int, output_dir: Path) -> Optional[Tuple[str, FigureData]]:
        """Process a figure or table element."""
        try:
            is_table = element.name == 'table'
            elem_type = 'tab' if is_table else 'fig'
            
            # Extract caption with proper LaTeX handling
            caption = element.find(['figcaption', 'caption'])
            caption_text = self._clean_latex_from_html(caption) if caption else ""
            
            # Get element ID
            number_match = re.search(rf'{elem_type}(?:ure)?\.?\s*(\d+)', caption_text.lower())
            fig_id = f"{elem_type}{number_match.group(1)}" if number_match else f"{elem_type}_{num}"

            # Clean up the caption - remove the original figure/table label and format our own
            if caption_text:
                # Remove the original figure/table label
                caption_text = re.sub(rf'^{elem_type}(?:ure)?\.?\s*\d+:?\s*', '', caption_text, flags=re.IGNORECASE)
                # Add our formatted label
                label_text = "Figure" if elem_type == "fig" else "Table"
                number = number_match.group(1) if number_match else num
                caption_text = f"**{label_text} {number}:** {caption_text}"

            if is_table:
                # Convert table to markdown
                table_md = self._table_to_markdown(element)
                if not table_md:
                    return None
                    
                figure_data = FigureData(
                    path=output_dir / f"{fig_id}.md",
                    caption=caption_text,
                    type='table',
                    content=table_md
                )
                
                # Save table markdown
                with open(figure_data.path, 'w', encoding='utf-8') as f:
                    f.write(table_md)
                
            else:
                # Process figure image
                img_data = self._process_figure_image(element)
                if not img_data:
                    return None
                
                output_path = output_dir / f"{fig_id}.png"
                img_data.save(output_path, format='PNG')
                
                figure_data = FigureData(
                    path=output_path,
                    caption=caption_text,
                    type='figure'
                )

            return fig_id, figure_data

        except Exception as e:
            self.logger.exception(f"Error processing element")
            return None

    def _process_figure_image(self, figure_elem: BeautifulSoup) -> Optional[Image.Image]:
        """Extract image from figure element."""
        # First try SVG
        svg = figure_elem.find('svg')
        if svg:
            return self._process_svg(svg)

        # Then try regular image
        img = figure_elem.find('img')
        if not img:
            return None
        
        src = img.get('src') or img.get('data-src')
        if not src:
            return None
        
        # Make relative URLs absolute
        if not src.startswith(('http://', 'https://', 'data:')):
            src = urljoin(self.current_base_url, src)
        
        if src.startswith('data:'):
            return self._decode_base64_image(src)
        else:
            return self._download_image(src)

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

    def _save_metadata(self, figures: Dict[str, FigureData], output_dir: Path):
        """Save figure/table metadata to JSON file."""
        metadata = {
            fig_id: {
                'path': str(data.path.relative_to(output_dir)),
                'caption': data.caption,
                'type': data.type,
                'content': data.content if data.type == 'table' else None
            }
            for fig_id, data in figures.items()
        }
        
        with open(output_dir / 'figures_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

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
        
        text = ""
        for child in element.children:
            if isinstance(child, Tag):
                if child.name == 'math':
                    # Get the LaTeX directly from alttext
                    latex = child.get('alttext', '')
                    if latex:
                        # Add inline math delimiters if not already present
                        if not latex.startswith('$') and not latex.endswith('$'):
                            text += f" ${latex}$ "
                        else:
                            text += f" {latex} "
                    else:
                        # Fallback to text content if no alttext
                        text += child.get_text()
                else:
                    text += self._clean_latex_from_html(child)
            else:
                # For text nodes, preserve them as-is
                text += str(child)
        
        # Clean up spacing around math delimiters
        text = re.sub(r'\s+\$', ' $', text)
        text = re.sub(r'\$\s+', '$ ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()