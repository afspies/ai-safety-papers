#!/usr/bin/env python3
"""Test Cloudflare R2 integration for AI Safety Papers."""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("r2_test")

def setup_environment():
    """Add the project root to the Python path."""
    project_root = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, project_root)
    logger.info(f"Added {project_root} to Python path")
    # Set PYTHONPATH environment variable
    os.environ['PYTHONPATH'] = project_root

def test_r2_upload():
    """Test uploading a file to Cloudflare R2."""
    from src.utils.cloudflare_r2 import CloudflareR2Client
    
    logger.info("Initializing CloudflareR2Client...")
    r2_client = CloudflareR2Client()
    
    # Create a test file content
    test_content = b"This is a test file for R2 integration."
    test_key = "test/test_file.txt"
    
    logger.info(f"Uploading test file to R2 with key: {test_key}")
    url = r2_client.upload_file(test_content, test_key, content_type="text/plain")
    
    if url:
        logger.info(f"Successfully uploaded file to R2. URL: {url}")
        
        # Test downloading the file
        logger.info("Testing download...")
        downloaded = r2_client.download_file(test_key)
        
        if downloaded == test_content:
            logger.info("Download test passed! Content matches.")
        else:
            logger.error("Download test failed! Content doesn't match.")
            return False
            
        # Test deleting the file
        logger.info("Testing deletion...")
        if r2_client.delete_file(test_key):
            logger.info("Deletion test passed!")
        else:
            logger.error("Deletion test failed!")
            return False
            
        return True
    else:
        logger.error("Failed to upload test file to R2.")
        return False

def test_figure_upload():
    """Test uploading a figure image to R2."""
    from src.utils.cloudflare_r2 import CloudflareR2Client
    
    # Look for a test image in the test data directory
    test_dir = Path("src/tests/test_data")
    if not test_dir.exists():
        logger.warning(f"Test directory {test_dir} not found. Skipping figure upload test.")
        return None
        
    # Find a figure image
    test_figures = list(test_dir.glob("*.png"))
    if not test_figures:
        # Try another common test location
        test_dir = Path("src/backend/src/tests/test_data")
        test_figures = list(test_dir.glob("*.png"))
        
    if not test_figures:
        # One more attempt to find a test image
        for root, dirs, files in os.walk("src"):
            for file in files:
                if file.endswith(".png"):
                    test_figures = [Path(os.path.join(root, file))]
                    break
            if test_figures:
                break
    
    if not test_figures:
        # Use the parsed_doc.json as a test file if no images are found
        test_file = test_dir / "parsed_doc.json"
        if test_file.exists():
            with open(test_file, "rb") as f:
                test_data = f.read()
            logger.info(f"Using {test_file} as test data (no PNG found)")
            
            r2_client = CloudflareR2Client()
            test_key = "test/test_doc.json"
            url = r2_client.upload_file(test_data, test_key, content_type="application/json")
            
            if url:
                logger.info(f"Successfully uploaded JSON to R2. URL: {url}")
                
                # Test downloading the file
                downloaded = r2_client.download_file(test_key)
                if downloaded == test_data:
                    logger.info("JSON download test passed!")
                else:
                    logger.error("JSON download test failed!")
                    
                # Clean up
                r2_client.delete_file(test_key)
                return url
            else:
                logger.error("Failed to upload JSON to R2.")
                return None
        
        logger.warning("No test images found. Skipping figure upload test.")
        return None
        
    # Read the test image
    test_fig = test_figures[0]
    logger.info(f"Using test image: {test_fig}")
    
    with open(test_fig, "rb") as f:
        image_data = f.read()
        
    # Upload to R2
    r2_client = CloudflareR2Client()
    test_key = f"test/test_figure.png"
    url = r2_client.upload_file(image_data, test_key, content_type="image/png")
    
    if url:
        logger.info(f"Successfully uploaded figure to R2. URL: {url}")
        
        # Test downloading the file
        downloaded = r2_client.download_file(test_key)
        if downloaded == image_data:
            logger.info("Figure download test passed!")
        else:
            logger.error("Figure download test failed!")
            
        # Clean up
        r2_client.delete_file(test_key)
        return url
    else:
        logger.error("Failed to upload figure to R2.")
        return None

def test_supabase_integration():
    """Test Supabase integration with Cloudflare R2."""
    try:
        from src.models.supabase import SupabaseDB
        from src.utils.cloudflare_r2 import CloudflareR2Client
        
        logger.info("Initializing Supabase client...")
        db = SupabaseDB()
        logger.info("Supabase client initialized successfully")
        
        # Generate a test paper ID for isolation
        import uuid
        test_paper_id = f"test_{uuid.uuid4().hex[:8]}"
        test_figure_id = "fig1"
        
        # Create a test image
        test_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00\x00\tpHYs\x00\x00\x0e\xc3\x00\x00\x0e\xc3\x01\xc7o\xa8d\x00\x00\x00=IDAT8Oc\xf8\xff\xff?\x03%\x80\x89\x81B@\xb1\x01 \xcd\x8c\x8c\x8c\xff\xe1\x06\xa0\x03t\x0bX\x18\x19\x19\xff\x83\xe4\xd0\x01\x10\x8f\x1a0j\xc0\xa8\x01\x18\x06\xa0\xa7\x01\n\xd3\x00\x00O\xbc\x0e\x03I\x94\xb9,\x00\x00\x00\x00IEND\xaeB`\x82'
        
        logger.info(f"Testing Supabase with test paper ID: {test_paper_id}")
        
        # Test adding a paper
        test_paper = {
            'id': test_paper_id,
            'title': 'Test Paper for R2 Integration',
            'authors': ['Test Author'],
            'abstract': 'This is a test paper for R2 integration testing.',
            'url': 'https://example.com/test_paper',
            'include_on_website': True,
            'highlight': False
        }
        
        logger.info("Adding test paper to Supabase...")
        result = db.add_paper(test_paper)
        if not result:
            logger.error("Failed to add test paper to Supabase")
            return False
        
        logger.info("Test paper added successfully")
        
        # Test adding a figure
        logger.info("Adding test figure to Supabase with R2 storage...")
        result = db.add_figure(test_paper_id, test_figure_id, test_image, caption="Test figure caption")
        if not result:
            logger.error("Failed to add test figure")
            return False
            
        logger.info("Test figure added successfully")
        
        # Test retrieving the figure URL
        logger.info("Retrieving figure URL...")
        url = db.get_figure_url(test_paper_id, test_figure_id)
        if not url:
            logger.error("Failed to retrieve figure URL")
            return False
            
        logger.info(f"Retrieved figure URL: {url}")
        
        # Test batch adding figures
        logger.info("Testing batch figure upload...")
        test_figures = [
            {
                'figure_id': 'fig2',
                'image_data': test_image,
                'caption': 'Test figure 2 caption',
                'content_type': 'image/png'
            },
            {
                'figure_id': 'fig3',
                'image_data': test_image,
                'caption': 'Test figure 3 caption',
                'content_type': 'image/png'
            }
        ]
        
        result = db.add_figures_batch(test_paper_id, test_figures)
        if not result:
            logger.error("Failed to batch add figures")
            return False
            
        logger.info("Batch figure upload successful")
        
        # Test retrieving all paper figures
        logger.info("Retrieving all paper figures...")
        figures = db.get_paper_figures(test_paper_id)
        if not figures or len(figures) < 3:  # We added 3 figures total
            logger.error(f"Failed to retrieve all paper figures. Got {len(figures) if figures else 0} figures.")
            return False
            
        logger.info(f"Retrieved {len(figures)} figures for paper")
        
        # Test adding a summary
        logger.info("Adding test summary...")
        display_figures = ['fig1', 'fig2']
        result = db.add_summary(test_paper_id, "This is a test summary for the paper.", display_figures, 'fig1')
        if not result:
            logger.error("Failed to add test summary")
            return False
            
        logger.info("Test summary added successfully")
        
        # Test retrieving the summary
        logger.info("Retrieving summary...")
        summary = db.get_summary(test_paper_id)
        if not summary:
            logger.error("Failed to retrieve summary")
            return False
            
        logger.info(f"Retrieved summary with {len(summary.get('display_figures', []))} display figures")
        
        # Clean up test data
        # Note: We're intentionally leaving the test data in Supabase for inspection
        # In a production environment, you'd want to clean up test data
        
        logger.info("Supabase integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in Supabase integration test: {e}")
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    setup_environment()
    logger.info("Starting R2 integration tests")
    
    # Test basic R2 operations
    if test_r2_upload():
        logger.info("R2 upload/download/delete tests passed!")
    else:
        logger.error("R2 upload/download/delete tests failed!")
        
    # Test figure upload
    figure_url = test_figure_upload()
    if figure_url:
        logger.info(f"Figure upload test passed! URL: {figure_url}")
    else:
        logger.warning("Figure upload test was skipped or failed.")
        
    # Test Supabase integration
    # We'll implement this once Supabase is set up
    test_supabase_integration()