import os
import logging
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

def split_pdf_at_appendix(pdf_path: Path, appendix_page_number: int) -> tuple[Path, Path]:
    """
    Split a PDF into two parts: main body and appendix.
    
    Args:
        pdf_path: Path to the input PDF file
        appendix_page_number: 1-based page number where the appendix begins
        
    Returns:
        Tuple containing:
        - Path to the body PDF
        - Path to the appendix PDF
    """
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if appendix_page_number is None:
        logger.info(f"No appendix page number provided for {pdf_path}. Using the full PDF.")
        return pdf_path, None
    
    try:
        # Create output file paths
        body_path = pdf_path.parent / "paper-body.pdf"
        appendix_path = pdf_path.parent / "paper-appendix.pdf"
        
        # Open the source PDF
        with open(pdf_path, 'rb') as f:
            pdf = PdfReader(f)
            total_pages = len(pdf.pages)
            
            # Validate appendix page number
            if appendix_page_number <= 0 or appendix_page_number > total_pages:
                logger.error(f"Invalid appendix page number {appendix_page_number} for PDF with {total_pages} pages")
                return pdf_path, None
            
            # Create body PDF (pages 0 to appendix_page_number-1)
            body_writer = PdfWriter()
            for page_num in range(0, appendix_page_number-1):
                body_writer.add_page(pdf.pages[page_num])
            
            # Create appendix PDF (pages appendix_page_number-1 to end)
            appendix_writer = PdfWriter()
            for page_num in range(appendix_page_number-1, total_pages):
                appendix_writer.add_page(pdf.pages[page_num])
            
            # Save the split PDFs
            with open(body_path, 'wb') as body_file:
                body_writer.write(body_file)
            
            with open(appendix_path, 'wb') as appendix_file:
                appendix_writer.write(appendix_file)
            
            logger.info(f"Successfully split PDF at page {appendix_page_number}")
            logger.info(f"Body PDF: {body_path} ({appendix_page_number-1} pages)")
            logger.info(f"Appendix PDF: {appendix_path} ({total_pages - (appendix_page_number-1)} pages)")
            
            return body_path, appendix_path
    except Exception as e:
        logger.error(f"Error splitting PDF {pdf_path}: {e}")
        return pdf_path, None 