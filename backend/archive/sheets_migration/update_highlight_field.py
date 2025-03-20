#!/usr/bin/env python3
import os
import sys
import logging
import re
from pathlib import Path
from sheets.sheets_db import SheetsDB
from utils.config_loader import load_config

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_highlight_in_markdown_files():
    """Update the highlight field in markdown files based on Google Sheets data."""
    logger.info("Starting to update highlight field in markdown files")
    
    try:
        config = load_config()
        
        sheets_db = SheetsDB(
            config['google_sheets']['spreadsheet_id'],
            config['google_sheets']['range_name'],
            config['google_sheets']['credentials_file']
        )
        
        # Get highlighted papers
        highlighted_papers = sheets_db.get_highlighted_papers()
        highlighted_ids = [paper['id'] for paper in highlighted_papers]
        
        logger.info(f"Found {len(highlighted_ids)} highlighted papers in sheets")
        logger.info(f"Highlighted paper IDs: {highlighted_ids}")
        
        # Update markdown files
        website_content_path = Path(project_root) / "ai-safety-site/content/en"
        posts_path = website_content_path / "posts"
        logger.info(f"Looking for posts in: {posts_path}")
        
        updated_count = 0
        
        # Get list of paper directories
        paper_dirs = list(posts_path.glob("paper_*"))
        logger.info(f"Found {len(paper_dirs)} paper directories")
        
        for paper_dir in paper_dirs:
            paper_id = paper_dir.name.replace("paper_", "")
            index_file = paper_dir / "index.md"
            
            # Log if this is a highlighted paper
            if paper_id in highlighted_ids:
                logger.info(f"Processing highlighted paper: {paper_id}")
            
            if not index_file.exists():
                continue
            
            is_highlighted = paper_id in highlighted_ids
            highlight_value = "true" if is_highlighted else "false"
            
            # Read the markdown file
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if highlight field exists
            highlight_exists = re.search(r'highlight:\s*(true|false)', content, re.IGNORECASE)
            
            if highlight_exists:
                # Update existing highlight field
                updated_content = re.sub(
                    r'(highlight:\s*)(true|false)',
                    f'\\1{highlight_value}',
                    content,
                    flags=re.IGNORECASE
                )
            else:
                # Add highlight field before math: true or before tags if they exist
                if "tags:" in content:
                    updated_content = re.sub(
                        r'(bookcase_cover_src:.*?\n)(tags:)',
                        f'\\1highlight: {highlight_value}\n\\2',
                        content,
                        flags=re.DOTALL
                    )
                else:
                    updated_content = re.sub(
                        r'(bookcase_cover_src:.*?\n)(math:\s*true)',
                        f'\\1highlight: {highlight_value}\n\\2',
                        content,
                        flags=re.DOTALL
                    )
                
                # If there was no match, try adding it before the end of the frontmatter
                if updated_content == content:
                    updated_content = re.sub(
                        r'(---\n.*?)\n(---)',
                        f'\\1\nhighlight: {highlight_value}\n\\2',
                        content,
                        flags=re.DOTALL
                    )
            
            # Write updated content back to file
            if content != updated_content:
                with open(index_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                updated_count += 1
                logger.info(f"Updated highlight field in {index_file} to {highlight_value}")
        
        logger.info(f"Updated highlight field in {updated_count} markdown files")
        
    except Exception as e:
        logger.error(f"Error updating highlight field: {e}")
        
if __name__ == "__main__":
    update_highlight_in_markdown_files()