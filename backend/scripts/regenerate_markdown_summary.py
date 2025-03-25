#!/usr/bin/env python
import argparse
import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.supabase import SupabaseDB
from src.summarizer.paper_summarizer import PaperSummarizer
from src.utils.figure_sync import inspect_and_sync_figures

def regenerate_markdown_summary(article_id: str, force_sync: bool = False):
    """
    Regenerate the markdown summary for a specific article.
    
    Args:
        article_id: The article ID
        force_sync: Whether to force sync figures before generating
    """
    db = SupabaseDB()
    
    # Sync figures if requested
    if force_sync:
        logger.info(f"Force syncing figures for article {article_id}")
        results = inspect_and_sync_figures(article_id)
        logger.info(f"Sync results: {len(results['sync_results'])} figures processed")
    
    # Get existing summary
    summary_data = db.get_summary(article_id)
    if not summary_data or not summary_data.get('summary'):
        logger.error(f"No summary found for article {article_id}")
        return False
    
    # Create summarizer
    summarizer = PaperSummarizer(db=db)
    
    # Generate markdown summary
    logger.info(f"Generating markdown summary for article {article_id}")
    markdown_summary = summarizer.post_process_summary_to_markdown(article_id, summary_data['summary'])
    
    # Update in Supabase
    logger.info(f"Updating markdown summary in Supabase for article {article_id}")
    db.add_summary(
        article_id,
        summary_data['summary'],
        summary_data['display_figures'],
        summary_data.get('thumbnail_figure'),
        markdown_summary
    )
    
    logger.info(f"Successfully regenerated markdown summary for article {article_id}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate markdown summary for an article")
    parser.add_argument("article_id", help="The article ID")
    parser.add_argument("--force-sync", action="store_true", help="Force sync figures before generating")
    
    args = parser.parse_args()
    
    success = regenerate_markdown_summary(args.article_id, args.force_sync)
    sys.exit(0 if success else 1) 