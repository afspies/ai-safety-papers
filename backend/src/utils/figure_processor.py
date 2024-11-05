import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from papermage.rasterizers import PDF2ImageRasterizer
from papermage import Document
import argparse
import json
import re

logger = logging.getLogger(__name__)

def setup_logging(debug: bool = True):
    """Set up logging configuration."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Quiet noisy loggers
    logging.getLogger('papermage').setLevel(logging.WARNING)
    logging.getLogger('pdfminer').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('pdf2image').setLevel(logging.WARNING)
    logging.getLogger('camelot').setLevel(logging.WARNING)
    logging.getLogger('pdfplumber').setLevel(logging.WARNING)
    logging.getLogger('pypdfium2').setLevel(logging.WARNING)

def load_or_parse_document(pdf_path: Path, cache_dir: Optional[Path] = None) -> Tuple[Document, Path]:
    """
    Load a parsed document from cache or parse it fresh if needed.
    
    Args:
        pdf_path: Path to the PDF file
        cache_dir: Directory to store parsed documents (defaults to pdf's parent dir)
        
    Returns:
        Tuple of (Parsed Document instance, Path to PDF file)
    """
    if cache_dir is None:
        cache_dir = pdf_path.parent
        
    # Create cache filename based on PDF path
    cache_path = cache_dir / f"{pdf_path.stem}_parsed.json"
    logger.debug(f"Looking for cached document at {cache_path}")
    
    if cache_path.exists():
        try:
            logger.debug("Found cached document, loading...")
            with open(cache_path, 'r') as f:
                doc = Document.from_json(json.load(f))
            logger.debug("Successfully loaded cached document")
            return doc, pdf_path
        except Exception as e:
            logger.warning(f"Failed to load cached document: {e}")
    
    # Parse document if not cached or cache loading failed
    logger.debug("Parsing document fresh...")
    from papermage.recipes import CoreRecipe
    recipe = CoreRecipe()
    doc = recipe.run(str(pdf_path))
    
    # Save to cache
    try:
        logger.debug("Saving parsed document to cache...")
        with open(cache_path, 'w') as f:
            json.dump(doc.to_json(), f, indent=4)
        logger.debug("Successfully cached parsed document")
    except Exception as e:
        logger.warning(f"Failed to cache parsed document: {e}")
    
    return doc, pdf_path

def parse_caption_label(caption_text: str) -> Optional[str]:
    """
    Extract figure or table label from caption text.
    
    Args:
        caption_text: The text of the caption
        
    Returns:
        Label (e.g., 'fig1', 'tab2') or None if no label found
    """
    # Clean and lowercase the text
    text = caption_text.lower().strip()
    
    # Common patterns for figure and table labels
    patterns = [
        # Figures
        r'^fig(?:ure)?\.?\s*(\d+[a-z]?)',  # Matches: Figure 1, Fig. 1, Fig 1a, etc.
        r'^figure\s*(\d+[a-z]?)',          # Matches: Figure 1, Figure 1b
        # Tables
        r'^tab(?:le)?\.?\s*(\d+[a-z]?)',   # Matches: Table 1, Tab. 1, Tab 1a, etc.
        r'^table\s*(\d+[a-z]?)',           # Matches: Table 1, Table 1b
        # Extended patterns
        r'^\(fig(?:ure)?\.?\s*(\d+[a-z]?)\)', # Matches: (Figure 1), (Fig. 1)
        r'^\(tab(?:le)?\.?\s*(\d+[a-z]?)\)',  # Matches: (Table 1), (Tab. 1)
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            number = match.group(1)
            # Determine if it's a figure or table
            if 'tab' in text[:4]:
                return f'tab{number}'
            else:
                return f'fig{number}'
    
    return None

def extract_figures(doc: Document, output_folder: Path, pdf_path: Path) -> Dict[str, Path]:
    """
    Extract figures from a parsed document.
    
    Args:
        doc: Parsed papermage Document
        output_folder: Where to save extracted figures
        pdf_path: Path to the original PDF file
        
    Returns:
        Dictionary mapping figure IDs to their saved paths
    """
    logger.debug(f"Extracting figures to {output_folder}")
    figures: Dict[str, Path] = {}
    
    try:
        rasterizer = PDF2ImageRasterizer()
        # Rasterize all pages at once
        rasterized_pages = rasterizer.rasterize(str(pdf_path), 300)
        
        for page_num, page in enumerate(doc.pages):
            logger.debug(f"Processing page {page_num}, found {len(page.images)} images")
            page_img = rasterized_pages[page_num].pilimage
            
            for fig_num, figure in enumerate(page.figures):
                internal_id = f"fig_{page_num}_{fig_num}"
                logger.debug(f"Processing {internal_id}")
                
                # Find associated caption
                caption = None
                caption_label = "unk"
                for cap in page.captions:
                    if cap.text:
                        caption = cap
                        # Try to extract label from caption
                        extracted_label = parse_caption_label(cap.text)
                        if extracted_label:
                            caption_label = extracted_label
                        logger.debug(f"Found caption for {internal_id}: {cap.text[:100]}...")
                        break
                
                if not caption:
                    logger.debug(f"No caption found for {internal_id}")
                    continue
                
                # Create figure ID that includes both internal ID and caption label
                figure_id = f"{internal_id}_{caption_label}"
                
                # Save the figure
                figure_path = output_folder / f"{figure_id}.png"
                try:
                    # Get bounding box of figure + caption
                    fig_bbox = figure.boxes[0]
                    l, t = fig_bbox.l, fig_bbox.t
                    r, b = fig_bbox.l + fig_bbox.w, fig_bbox.t + fig_bbox.h
                    
                    caption_bbox = caption.boxes[0]
                    l = min(l, caption_bbox.l)
                    t = min(t, caption_bbox.t)
                    r = max(r, caption_bbox.l + caption_bbox.w)
                    b = max(b, caption_bbox.t + caption_bbox.h)
                    
                    # Add margins
                    l, t = l - 0.01, t - 0.01
                    r, b = r + 0.01, b + 0.01
                    
                    # Convert to pixels
                    bbox = [
                        int(l * page_img.size[0]),
                        int(t * page_img.size[1]),
                        int(r * page_img.size[0]),
                        int(b * page_img.size[1])
                    ]
                    
                    # Crop and save figure
                    fig_img = page_img.crop(bbox)
                    if fig_img.size[0] > 0 and fig_img.size[1] > 0:
                        fig_img.save(figure_path)
                        figures[figure_id] = figure_path
                        logger.debug(f"Saved figure to {figure_path}")
                    else:
                        logger.warning(f"Invalid figure dimensions for {figure_id}")
                        
                except Exception as e:
                    logger.error(f"Failed to save figure {figure_id}: {e}")
                    
    except Exception as e:
        logger.error(f"Error during figure extraction: {e}")
        
    return figures

def create_thumbnail(
    pdf_path: Path,
    output_path: Path,
    mode: str = 'full',
    doc: Optional[Document] = None
) -> Optional[Path]:
    """
    Create a thumbnail from the first page of a PDF.
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Where to save the thumbnail
        mode: 'full' or 'abstract'
        doc: Optional parsed Document for abstract detection
        
    Returns:
        Path to created thumbnail or None if failed
    """
    logger.debug(f"Creating thumbnail from {pdf_path} in {mode} mode")
    
    try:
        logger.debug("Initializing PDF rasterizer...")
        rasterizer = PDF2ImageRasterizer()
        logger.debug("Rasterizing first page...")
        rasterized_image = rasterizer.rasterize(str(pdf_path), 300)
        
        if not rasterized_image or not rasterized_image[0]:
            raise ValueError("Rasterization failed")
            
        page_image = rasterized_image[0].pilimage
        im_w, im_h = page_image.size
        logger.debug(f"Page dimensions: {im_w}x{im_h}")
        
        # Calculate bounds based on mode
        if mode == 'full':
            l, t = 0.075, 0.075  # Small margin from edges
            w, h = 0.85, 0.3     # Wide width, moderate height
            
            # Try to use abstract for bottom bound if available
            if doc and doc.pages and doc.pages[0].abstracts:
                abstract_bbox = doc.pages[0].abstracts[0].boxes[0]
                h = (abstract_bbox.t + abstract_bbox.h + 0.01) - t
                logger.debug(f"Using abstract bottom bound, height={h:.2f}")
            
            logger.debug("Using full-width bounds")
            
        else:  # abstract mode
            l, t = 0.1, 0.1
            w, h = 0.8, 0.3
            
            if doc and doc.pages and doc.pages[0].abstracts:
                abstract_bbox = doc.pages[0].abstracts[0].boxes[0]
                l, t = abstract_bbox.l, abstract_bbox.t
                w, h = abstract_bbox.w, abstract_bbox.h
                logger.debug(f"Using abstract bounds: l={l:.2f}, t={t:.2f}, w={w:.2f}, h={h:.2f}")
            else:
                logger.debug("No abstract found, using default bounds")
        
        # Convert to pixels
        bbox = [
            int(l * im_w),
            int(t * im_h),
            int((l + w) * im_w),
            int((t + h) * im_h)
        ]
        logger.debug(f"Crop bbox: {bbox}")
        
        # Crop and save
        cropped = page_image.crop(bbox)
        cropped.save(output_path)
        logger.debug(f"Saved thumbnail to {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to create thumbnail: {e}")
        return None

def test_figure_processing(pdf_path: str, output_dir: str):
    """Test figure processing on a single PDF."""
    setup_logging(True)
    logger.info(f"Testing figure processing on {pdf_path}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create test directories
        figures_dir = output_path / "figures"
        figures_dir.mkdir(exist_ok=True)
        
        # Load or parse document
        pdf_path_obj = Path(pdf_path)
        doc, pdf_path_obj = load_or_parse_document(pdf_path_obj, output_path)
        logger.info(f"Successfully loaded/parsed document with {len(doc.pages)} pages")
        
        # Extract figures
        figures = extract_figures(doc, figures_dir, pdf_path_obj)
        logger.info(f"Extracted {len(figures)} figures")
        
        # Create thumbnails in both modes
        for mode in ['full', 'abstract']:
            thumb_path = output_path / f"thumbnail_{mode}.png"
            result = create_thumbnail(
                Path(pdf_path),
                thumb_path,
                mode=mode,
                doc=doc
            )
            if result:
                logger.info(f"Created {mode} thumbnail at {thumb_path}")
            else:
                logger.error(f"Failed to create {mode} thumbnail")
                
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test figure processing")
    parser.add_argument("pdf_path", help="Path to PDF file to process")
    parser.add_argument("--output", "-o", default="./test_output",
                       help="Output directory for processed figures")
    
    args = parser.parse_args()
    test_figure_processing(args.pdf_path, args.output) 