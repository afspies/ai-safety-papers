import logging
import importlib.util

# Check if PyMuPDF is installed
PYMUPDF_AVAILABLE = importlib.util.find_spec("fitz") is not None
if PYMUPDF_AVAILABLE:
    import fitz  # PyMuPDF
else:
    logging.warning("PyMuPDF not installed. PDF figure extraction will not be available.")
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re
import os
from PIL import Image
import io
import numpy as np
from backend.src.models.figure import Figure, FigureExtractor

logger = logging.getLogger(__name__)

class PdfFigureExtractor(FigureExtractor):
    """Figure extractor using PyMuPDF to extract images from PDF files."""
    
    def __init__(self, resolution: int = 300):
        self.logger = logger
        self.resolution = resolution  # DPI for rendering
    
    def extract_figures(self, source_path: Path, output_dir: Path) -> List[Figure]:
        """
        Extract figures from a PDF file.
        
        Args:
            source_path: Path to the PDF file
            output_dir: Directory to save extracted figures
            
        Returns:
            List of Figure objects
        """
        if not PYMUPDF_AVAILABLE:
            self.logger.error("PyMuPDF not installed. Cannot extract figures from PDF.")
            return []
            
        try:
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Open PDF file
            self.logger.info(f"Opening PDF file: {source_path}")
            doc = fitz.Document(source_path)
            
            # Extract text to find figure captions
            self.logger.info("Extracting text to find figure captions")
            captions = self._extract_figure_captions(doc)
            
            # Extract images
            self.logger.info("Extracting images from PDF")
            figures = []
            
            # Try two different methods to extract images
            images_method1 = self._extract_images_method1(doc, output_dir)
            if images_method1:
                self.logger.info(f"Extracted {len(images_method1)} images using method 1")
                figures.extend(self._match_images_to_captions(images_method1, captions))
            
            # Only use method 2 if method 1 didn't find enough images
            if len(images_method1) < len(captions):
                images_method2 = self._extract_images_method2(doc, output_dir)
                if images_method2:
                    self.logger.info(f"Extracted {len(images_method2)} images using method 2")
                    # Only consider images that weren't found by method 1
                    new_images = [img for img in images_method2 if not any(
                        os.path.basename(img['path']) == os.path.basename(old_img['path'])
                        for old_img in images_method1
                    )]
                    self.logger.info(f"Found {len(new_images)} new images with method 2")
                    figures.extend(self._match_images_to_captions(new_images, captions))
            
            # Close the document
            doc.close()
            
            # Create Figure objects from extracted data
            figure_objects = []
            for fig in figures:
                try:
                    figure = Figure(
                        id=fig['id'],
                        caption=fig['caption'],
                        has_subfigures=False,  # PDF extraction doesn't handle subfigures well
                        type="figure",
                        path=fig['path']
                    )
                    figure_objects.append(figure)
                except Exception as e:
                    self.logger.warning(f"Error creating Figure object: {e}")
            
            self.logger.info(f"Created {len(figure_objects)} Figure objects")
            return figure_objects
            
        except Exception as e:
            self.logger.error(f"Error extracting figures from PDF: {e}")
            return []
    
    def _extract_figure_captions(self, doc) -> Dict[str, str]:
        """
        Extract figure captions from PDF document.
        
        Returns:
            Dictionary mapping figure IDs to captions
        """
        captions = {}
        caption_pattern = re.compile(r'(Figure|Fig\.?)\s+(\d+[a-zA-Z]?)[\.\:]?\s+(.+?)(?=Figure|Fig\.?|$)', re.IGNORECASE | re.DOTALL)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            for match in caption_pattern.finditer(text):
                prefix, fig_num, caption_text = match.groups()
                fig_id = f"fig{fig_num}"
                caption = caption_text.strip().replace('\n', ' ')
                captions[fig_id] = caption
        
        self.logger.info(f"Found {len(captions)} figure captions")
        return captions
    
    def _extract_images_method1(self, doc, output_dir: Path) -> List[Dict[str, Any]]:
        """
        Extract images using PyMuPDF's getImageList and extractImage methods.
        
        Returns:
            List of dictionaries with image data
        """
        images = []
        seen_xrefs = set()
        
        for page_num, page in enumerate(doc):
            image_list = page.get_images(full=True)
            
            for img_idx, img_info in enumerate(image_list):
                xref = img_info[0]
                
                # Skip duplicate images
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                
                try:
                    # Try to extract the image by xref
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image['image']
                    
                    # Filter out small images (likely icons, bullets, etc.)
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    width, height = pil_img.size
                    
                    # Skip small images (likely not figures)
                    if width < 100 or height < 100:
                        continue
                    
                    # Save the image
                    img_path = output_dir / f"pdf_img_{page_num+1}_{img_idx+1}.png"
                    with open(img_path, 'wb') as f:
                        f.write(image_bytes)
                    
                    images.append({
                        'path': img_path,
                        'page': page_num,
                        'index': img_idx,
                        'width': width,
                        'height': height
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error extracting image on page {page_num+1}: {e}")
        
        return images
    
    def _extract_images_method2(self, doc, output_dir: Path) -> List[Dict[str, Any]]:
        """
        Extract images by rendering PDF pages to pixmaps and using image processing
        to detect and extract image regions.
        
        Returns:
            List of dictionaries with image data
        """
        images = []
        
        for page_num, page in enumerate(doc):
            try:
                # Render page to pixmap
                pix = page.get_pixmap(matrix=fitz.Matrix(self.resolution/72, self.resolution/72))
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                pil_img = Image.open(io.BytesIO(img_data))
                
                # Save full page for reference
                page_path = output_dir / f"pdf_page_{page_num+1}.png"
                pil_img.save(page_path)
                
                # Use full page as an image (as fallback)
                images.append({
                    'path': page_path,
                    'page': page_num,
                    'index': 0,
                    'width': pil_img.width,
                    'height': pil_img.height
                })
                
                # TODO: Implement more sophisticated image region detection
                # This would involve using image processing to find figure boundaries
                # For now, we just use the full page as a fallback
                
            except Exception as e:
                self.logger.warning(f"Error processing page {page_num+1}: {e}")
        
        return images
    
    def _match_images_to_captions(self, images: List[Dict[str, Any]], captions: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Match extracted images to their captions based on position and content.
        
        Returns:
            List of dictionaries with image data and captions
        """
        result = []
        
        # Sort images by page number and position
        sorted_images = sorted(images, key=lambda x: (x['page'], x.get('index', 0)))
        
        # Sort captions by figure number
        sorted_captions = sorted(
            [(fig_id, caption) for fig_id, caption in captions.items()], 
            key=lambda x: int(re.match(r'fig(\d+)', x[0]).group(1))
        )
        
        # Match images to captions in order
        # This is a simple heuristic - figures usually appear in order
        for i, ((fig_id, caption), image) in enumerate(zip(sorted_captions, sorted_images)):
            result.append({
                'id': fig_id,
                'caption': caption,
                'path': image['path'],
                'page': image['page']
            })
        
        # Add any remaining images without captions
        for i, image in enumerate(sorted_images[len(result):]):
            result.append({
                'id': f"fig{len(result) + 1}",
                'caption': f"Figure {len(result) + 1}",
                'path': image['path'],
                'page': image['page']
            })
        
        return result