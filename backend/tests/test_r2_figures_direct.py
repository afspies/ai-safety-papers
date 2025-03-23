#!/usr/bin/env python3
"""
Test Cloudflare R2 integration for figures directly.
This script performs R2 operations directly without Supabase.
"""

import os
import sys
import logging
from pathlib import Path
import json
from PIL import Image
import io
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("r2_figures_test")

def setup_environment():
    """Add the project root to the Python path."""
    project_root = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, project_root)
    logger.info(f"Added {project_root} to Python path")

def find_test_figures():
    """Find test figures in the repository for testing."""
    base_dirs = [
        "src/tests/data",
        "src/tests/test_data",
        "data"
    ]
    
    figures = []
    for base_dir in base_dirs:
        base_path = Path(base_dir)
        if not base_path.exists():
            continue
        
        # Look for figures in subfolders
        for paper_dir in base_path.glob("*"):
            if not paper_dir.is_dir():
                continue
                
            # Check for figures directory
            figures_dir = paper_dir / "figures"
            if figures_dir.exists() and figures_dir.is_dir():
                png_files = list(figures_dir.glob("*.png"))
                if png_files:
                    # Get paper_id from directory name
                    paper_id = paper_dir.name
                    figures.append({
                        "paper_id": paper_id,
                        "figures_dir": figures_dir,
                        "png_files": png_files
                    })
    
    return figures

def upload_figure_to_r2(r2_client, paper_id, figure_path):
    """Upload a figure to R2 without Supabase."""
    try:
        # Read the figure
        with open(figure_path, 'rb') as f:
            image_data = f.read()
        
        # Extract figure ID from filename
        figure_id = figure_path.stem
        
        # Create R2 key
        r2_key = f"figures/{paper_id}/{figure_id}.png"
        
        # Upload to R2
        logger.info(f"Uploading figure {figure_id} for paper {paper_id}")
        r2_url = r2_client.upload_file(image_data, r2_key, content_type="image/png")
        
        if r2_url:
            logger.info(f"Successfully uploaded figure to R2: {r2_url}")
            return r2_url
        else:
            logger.error(f"Failed to upload figure {figure_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error uploading figure {figure_path}: {e}")
        return None

def test_r2_figures_upload():
    """Test uploading figures to R2."""
    try:
        # Import the R2 client
        from src.utils.cloudflare_r2 import CloudflareR2Client
        r2_client = CloudflareR2Client()
        
        # Find test figures
        logger.info("Finding test figures...")
        figure_sets = find_test_figures()
        
        if not figure_sets:
            logger.warning("No test figures found. Skipping upload test.")
            return
            
        logger.info(f"Found {len(figure_sets)} paper directories with figures")
        
        # Process each set of figures
        for figure_set in figure_sets:
            paper_id = figure_set["paper_id"]
            figures_dir = figure_set["figures_dir"]
            png_files = figure_set["png_files"]
            
            logger.info(f"Processing {len(png_files)} figures for paper {paper_id}")
            
            # Upload each figure
            uploads = []
            for png_file in png_files:
                r2_url = upload_figure_to_r2(r2_client, paper_id, png_file)
                if r2_url:
                    uploads.append({
                        "figure_id": png_file.stem,
                        "r2_url": r2_url
                    })
            
            # Create a figures.json file with R2 URLs
            if uploads:
                r2_meta = {}
                for upload in uploads:
                    r2_meta[upload["figure_id"]] = {
                        "r2_url": upload["r2_url"]
                    }
                
                # Save to figures_r2.json
                output_file = figures_dir / "figures_r2.json"
                with open(output_file, 'w') as f:
                    json.dump(r2_meta, f, indent=2)
                logger.info(f"Saved R2 metadata to {output_file}")
                
            logger.info(f"Uploaded {len(uploads)}/{len(png_files)} figures for paper {paper_id}")
            
    except Exception as e:
        logger.error(f"Error during R2 upload test: {e}")
        return False

def upload_test_figures(paper_id, figures_dir):
    """
    Upload figures from a specific directory to R2.
    
    Args:
        paper_id: Paper ID to use for storage
        figures_dir: Directory containing figures to upload
    """
    try:
        # Import the R2 client
        from src.utils.cloudflare_r2 import CloudflareR2Client
        r2_client = CloudflareR2Client()
        
        # Check if directory exists
        figures_path = Path(figures_dir)
        if not figures_path.exists() or not figures_path.is_dir():
            logger.error(f"Figures directory {figures_dir} does not exist or is not a directory")
            return False
        
        # Find PNG files
        png_files = list(figures_path.glob("*.png"))
        if not png_files:
            logger.warning(f"No PNG files found in {figures_dir}")
            return False
            
        logger.info(f"Found {len(png_files)} PNG files in {figures_dir}")
        
        # Upload each figure
        uploads = []
        for png_file in png_files:
            r2_url = upload_figure_to_r2(r2_client, paper_id, png_file)
            if r2_url:
                uploads.append({
                    "figure_id": png_file.stem,
                    "r2_url": r2_url
                })
        
        # Create a figures.json file with R2 URLs
        if uploads:
            r2_meta = {}
            for upload in uploads:
                r2_meta[upload["figure_id"]] = {
                    "r2_url": upload["r2_url"]
                }
            
            # Save to figures_r2.json
            output_file = figures_path / "figures_r2.json"
            with open(output_file, 'w') as f:
                json.dump(r2_meta, f, indent=2)
            logger.info(f"Saved R2 metadata to {output_file}")
            
        logger.info(f"Uploaded {len(uploads)}/{len(png_files)} figures for paper {paper_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error uploading test figures: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test R2 figure uploads")
    parser.add_argument("--paper-id", help="Paper ID to use for uploads")
    parser.add_argument("--figures-dir", help="Directory containing figures to upload")
    parser.add_argument("--auto", action="store_true", help="Auto-discover and upload all test figures")
    
    args = parser.parse_args()
    setup_environment()
    
    if args.auto:
        logger.info("Auto-discovering and uploading test figures")
        test_r2_figures_upload()
    elif args.paper_id and args.figures_dir:
        logger.info(f"Uploading figures for paper {args.paper_id} from {args.figures_dir}")
        upload_test_figures(args.paper_id, args.figures_dir)
    else:
        logger.error("Either use --auto or provide both --paper-id and --figures-dir")
        parser.print_help()
        sys.exit(1)