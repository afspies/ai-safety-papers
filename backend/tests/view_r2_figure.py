#!/usr/bin/env python3
"""View a figure from Cloudflare R2 storage."""

import sys
import os
import argparse
import logging
from pathlib import Path
import tempfile
import base64
import json
import webbrowser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("r2_figure_viewer")

def setup_environment():
    """Add the project root to the Python path."""
    project_root = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, project_root)
    logger.info(f"Added {project_root} to Python path")

def view_figure_from_r2(paper_id, figure_id):
    """
    Download and view a figure from Cloudflare R2.
    
    Args:
        paper_id: The paper ID
        figure_id: The figure ID
    """
    try:
        # Import the R2 client
        from src.utils.cloudflare_r2 import CloudflareR2Client
        r2_client = CloudflareR2Client()
        
        # Create the R2 key
        r2_key = f"figures/{paper_id}/{figure_id}.png"
        
        # Try to download the figure
        logger.info(f"Downloading figure: {r2_key}")
        image_data = r2_client.download_file(r2_key)
        
        if not image_data:
            logger.error(f"Figure not found: {r2_key}")
            return False
            
        logger.info(f"Downloaded {len(image_data)} bytes")
        
        # Save to a temporary file and open with default viewer
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(image_data)
            tmp_path = tmp.name
            
        logger.info(f"Saved to temporary file: {tmp_path}")
        logger.info("Opening figure for viewing...")
        
        # Try to open with the default image viewer
        try:
            webbrowser.open(f"file://{tmp_path}")
        except Exception as e:
            logger.error(f"Failed to open figure: {e}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error viewing figure: {e}")
        return False

def get_r2_url(paper_id, figure_id):
    """
    Get the R2 URL for a figure without downloading it.
    
    Args:
        paper_id: The paper ID
        figure_id: The figure ID
    """
    try:
        # Import the R2 client
        from src.utils.cloudflare_r2 import CloudflareR2Client
        r2_client = CloudflareR2Client()
        
        # Generate a presigned URL with 24 hour expiration
        r2_key = f"figures/{paper_id}/{figure_id}.png"
        url = r2_client.generate_presigned_url(r2_key, 86400)
        
        if url:
            logger.info(f"Generated URL for figure: {url}")
            return url
        else:
            logger.error(f"Failed to generate URL for figure: {r2_key}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating URL: {e}")
        return None

def list_r2_figures(paper_id=None):
    """
    List figures available in R2 storage.
    
    Args:
        paper_id: Optional paper ID to filter by
    """
    try:
        # Check for local R2 metadata files
        paper_dirs = []
        
        # Look for test_r2_upload directories
        base_dir = Path("test_r2_upload")
        if base_dir.exists() and base_dir.is_dir():
            paper_dirs.append({
                "paper_id": "test-paper",
                "dir": base_dir
            })
            
        # Look for figures_r2.json in test_r2_upload
        if base_dir.exists() and base_dir.is_dir():
            figures_dir = base_dir / "figures"
            r2_meta_file = figures_dir / "figures_r2.json"
            if r2_meta_file.exists():
                with open(r2_meta_file, 'r') as f:
                    r2_meta = json.load(f)
                    for fig_id, meta in r2_meta.items():
                        if 'r2_url' in meta:
                            r2_url = meta['r2_url']
                            logger.info(f"Figure {fig_id} (paper test-paper): {r2_url}")
        
        if paper_id:
            # Just grab the presigned URL for the specified paper+figure
            url = get_r2_url(paper_id, figure_id)
            if url:
                logger.info(f"URL for {paper_id}/{figure_id}: {url}")
                return True
            else:
                logger.error(f"Failed to get URL for {paper_id}/{figure_id}")
                return False
        
        if not paper_dirs:
            logger.warning("No R2 metadata files found.")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error listing figures: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View figures from Cloudflare R2")
    parser.add_argument("--paper-id", help="Paper ID to view figures from")
    parser.add_argument("--figure-id", help="Figure ID to view")
    parser.add_argument("--url", action="store_true", help="Get URL instead of downloading")
    parser.add_argument("--list", action="store_true", help="List available figures")
    
    args = parser.parse_args()
    setup_environment()
    
    if args.list:
        logger.info("Listing available figures")
        list_r2_figures(args.paper_id)
    elif args.paper_id and args.figure_id:
        if args.url:
            logger.info(f"Getting URL for figure {args.figure_id} in paper {args.paper_id}")
            get_r2_url(args.paper_id, args.figure_id)
        else:
            logger.info(f"Viewing figure {args.figure_id} from paper {args.paper_id}")
            view_figure_from_r2(args.paper_id, args.figure_id)
    else:
        logger.error("Either use --list or provide both --paper-id and --figure-id")
        parser.print_help()
        sys.exit(1)