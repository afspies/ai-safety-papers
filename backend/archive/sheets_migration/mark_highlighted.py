#!/usr/bin/env python3
import os
import sys
import logging
from sheets.sheets_db import SheetsDB
from utils.config_loader import load_config

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Mark a few papers as highlighted for testing."""
    logger.info("Starting to mark papers as highlighted")
    
    try:
        config = load_config()
        
        sheets_db = SheetsDB(
            config['google_sheets']['spreadsheet_id'],
            config['google_sheets']['range_name'],
            config['google_sheets']['credentials_file']
        )
        
        # Get all records
        all_records = sheets_db.worksheet.get_all_records()
        
        # Take first 3 papers with Include on Website = TRUE
        highlighted_count = 0
        total_updated = 0
        
        for i, row in enumerate(all_records):
            if row.get('Include on Website') == 'TRUE':
                row_idx = i + 2  # +2 because sheets are 1-indexed and we have a header row
                paper_id = row.get('Paper ID')
                
                if highlighted_count < 3:
                    # Mark as highlighted
                    sheets_db.worksheet.update_cell(row_idx, sheets_db.COLUMN_MAP['highlight'] + 1, 'TRUE')
                    logger.info(f"Marked paper {paper_id} as highlighted")
                    highlighted_count += 1
                    total_updated += 1
                    
                if highlighted_count >= 3:
                    break
                    
        logger.info(f"Marked {total_updated} papers as highlighted")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        
if __name__ == "__main__":
    main()