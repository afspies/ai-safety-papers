#!/usr/bin/env python3
"""
Setup script to create the 'papers' table in Supabase.
"""
import os
import sys
import argparse
import logging
from supabase import create_client

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Create the papers table in Supabase.
    """
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Setup Supabase table')
        parser.add_argument('--url', required=True, help='Supabase URL')
        parser.add_argument('--key', required=True, help='Supabase service_role key (not anon key)')
        args = parser.parse_args()
        
        logger.info("Connecting to Supabase...")
        supabase = create_client(args.url, args.key)
        
        # SQL for creating the papers table
        table_sql = """
        CREATE TABLE IF NOT EXISTS papers (
            id text PRIMARY KEY,
            title text NOT NULL,
            authors text[] DEFAULT '{}',
            year text,
            abstract text DEFAULT '',
            url text DEFAULT '',
            venue text DEFAULT '',
            tldr text DEFAULT '',
            submitted_date timestamp with time zone,
            highlight boolean DEFAULT false,
            include_on_website boolean DEFAULT false,
            post_to_bots boolean DEFAULT false,
            posted_date timestamp with time zone,
            ai_safety_relevance integer DEFAULT 0,
            mech_int_relevance integer DEFAULT 0,
            embedding_model text DEFAULT '',
            embedding_vector float[] DEFAULT '{}',
            tags text[] DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS papers_highlight_idx ON papers (highlight);
        CREATE INDEX IF NOT EXISTS papers_include_on_website_idx ON papers (include_on_website);
        """
        
        logger.info("Creating papers table and indexes...")
        # You'll need to use the special rpc function to execute SQL
        supabase.rpc('exec_sql', {'sql': table_sql}).execute()
        
        logger.info("Table setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error setting up Supabase table: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()