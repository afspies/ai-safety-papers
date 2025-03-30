#!/usr/bin/env python3
"""Simple test for Cloudflare R2 functionality."""

import os
import sys
import logging
from pathlib import Path
from PIL import Image
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("r2_simple_test")

def setup_environment():
    """Add the project root to the Python path."""
    project_root = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, project_root)
    logger.info(f"Added {project_root} to Python path")

def test_r2_upload_image():
    """
    Test Cloudflare R2 upload with a simple generated image.
    """
    # Import the R2 client
    try:
        from src.utils.cloudflare_r2 import CloudflareR2Client
    except ImportError:
        logger.error("Failed to import CloudflareR2Client")
        return False
    
    try:
        # Create a simple test image
        logger.info("Creating test image...")
        width, height = 200, 200
        img = Image.new('RGB', (width, height), color='white')
        
        # Draw something on the image
        for x in range(width):
            for y in range(height):
                if (x + y) % 20 == 0:
                    img.putpixel((x, y), (255, 0, 0))  # Red pixel
        
        # Add a border
        for x in range(width):
            img.putpixel((x, 0), (0, 0, 255))  # Blue pixel
            img.putpixel((x, height-1), (0, 0, 255))  # Blue pixel
        
        for y in range(height):
            img.putpixel((0, y), (0, 0, 255))  # Blue pixel
            img.putpixel((width-1, y), (0, 0, 255))  # Blue pixel
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        # Initialize the R2 client
        logger.info("Initializing R2 client...")
        r2_client = CloudflareR2Client()
        
        # Upload the image
        test_key = "test/simple_test_image.png"
        logger.info(f"Uploading test image with key: {test_key}")
        url = r2_client.upload_file(img_data, test_key, content_type="image/png")
        
        if url:
            logger.info(f"Successfully uploaded image to R2: {url}")
            
            # Try to download the image back
            logger.info("Testing download...")
            downloaded = r2_client.download_file(test_key)
            
            if downloaded and downloaded == img_data:
                logger.info("Download test passed! Content matches.")
            else:
                logger.error("Download test failed! Content doesn't match or is None.")
                return False
            
            # Clean up by deleting the test file
            logger.info("Testing deletion...")
            if r2_client.delete_file(test_key):
                logger.info("Successfully deleted test file.")
            else:
                logger.warning("Failed to delete test file.")
            
            return True
        else:
            logger.error("Failed to upload test image.")
            return False
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    setup_environment()
    logger.info("Starting simple R2 test")
    
    if test_r2_upload_image():
        logger.info("Simple R2 test passed!")
    else:
        logger.error("Simple R2 test failed.")
        sys.exit(1)