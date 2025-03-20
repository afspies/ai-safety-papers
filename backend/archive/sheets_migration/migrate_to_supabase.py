#!/usr/bin/env python3
"""
Migration script to transfer data from Google Sheets to Supabase.
Uses the Supabase API client for data migration.
"""
import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from pathlib import Path
from supabase import create_client, Client

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from backend.src.utils.config_loader import load_config
from backend.src.sheets.sheets_db import SheetsDB

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)

def migrate_data(sheets_db, supabase_client):
    """
    Migrate data from Google Sheets to Supabase.
    
    Args:
        sheets_db: Google Sheets database client
        supabase_client: Supabase client
    """
    try:
        # Get all records from Google Sheets
        logger.info("Fetching all records from Google Sheets...")
        all_records = sheets_db.worksheet.get_all_records()
        logger.info(f"Found {len(all_records)} records in Google Sheets")
        
        # Process records for Supabase
        success_count = 0
        error_count = 0
        
        # Process and insert records in batches to prevent timeouts
        batch_size = 10
        current_batch = []
        
        for i, row in enumerate(all_records):
            try:
                # Skip rows without a Paper ID
                if not row.get('Paper ID'):
                    logger.warning(f"Skipping row {i+1} without Paper ID")
                    continue
                
                # Parse date fields
                submitted_date = None
                if row.get('Submitted Date'):
                    try:
                        submitted_date = datetime.strptime(row['Submitted Date'], "%d/%m/%Y").isoformat()
                    except ValueError:
                        logger.warning(f"Invalid submitted date format for paper {row['Paper ID']}")
                
                posted_date = None
                if row.get('Posted Date'):
                    try:
                        posted_date = datetime.strptime(row['Posted Date'], "%d/%m/%Y").isoformat()
                    except ValueError:
                        logger.warning(f"Invalid posted date format for paper {row['Paper ID']}")
                
                # Parse embedding vector
                embedding_vector = []
                if row.get('Embedding Vector'):
                    try:
                        embedding_vector = json.loads(row['Embedding Vector'])
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid embedding vector for paper {row['Paper ID']}")
                
                # Create record for Supabase
                paper = {
                    'id': row['Paper ID'],
                    'title': row['Title'],
                    'authors': row['Authors'].split(', ') if row['Authors'] else [],
                    'year': row['Year'],
                    'abstract': row['Abstract'],
                    'url': row['URL'],
                    'venue': row['Venue'],
                    'tldr': row['TLDR'],
                    'submitted_date': submitted_date,
                    'highlight': row.get('Highlight') == 'TRUE',
                    'include_on_website': row.get('Include on Website') == 'TRUE',
                    'post_to_bots': row.get('Post to Bots') == 'TRUE',
                    'posted_date': posted_date,
                    'ai_safety_relevance': int(row.get('AI Safety Relevance', 0)),
                    'mech_int_relevance': int(row.get('Mech Int Relevance', 0)),
                    'embedding_model': row.get('Embedding Model', ''),
                    'embedding_vector': embedding_vector if embedding_vector else [],
                    'tags': []  # No tags in the original schema
                }
                
                current_batch.append(paper)
                
                # Process batch when it reaches batch_size or at the end
                if len(current_batch) >= batch_size or i == len(all_records) - 1:
                    logger.info(f"Inserting batch of {len(current_batch)} records (papers {success_count+1} to {success_count+len(current_batch)})...")
                    result = supabase_client.table('papers').upsert(current_batch).execute()
                    
                    success_count += len(current_batch)
                    current_batch = []  # Reset batch
                    
                    # Log progress
                    logger.info(f"Progress: {success_count}/{len(all_records)} records processed")
                
            except Exception as e:
                logger.error(f"Error processing row {i+1} with Paper ID {row.get('Paper ID', 'unknown')}: {e}")
                error_count += 1
                continue
        
        logger.info(f"Migration complete: {success_count} records successfully migrated, {error_count} errors")
    
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        sys.exit(1)

def main():
    """
    Main function to run the migration.
    """
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Migrate data from Google Sheets to Supabase')
        parser.add_argument('--url', required=True, help='Supabase URL')
        parser.add_argument('--key', required=True, help='Supabase API key')
        args = parser.parse_args()
        
        logger.info("Starting migration from Google Sheets to Supabase")
        
        # Load config
        config = load_config()
        
        # Initialize Google Sheets client
        sheets_db = SheetsDB(
            config['google_sheets']['spreadsheet_id'],
            config['google_sheets']['range_name'],
            config['google_sheets']['credentials_file']
        )
        logger.info("Initialized Google Sheets client")
        
        # Initialize Supabase client
        supabase = create_client(args.url, args.key)
        logger.info("Initialized Supabase client")
        
        # Migrate data
        migrate_data(sheets_db, supabase)
        
        logger.info("Migration successfully completed")
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()