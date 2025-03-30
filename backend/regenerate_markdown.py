#!/usr/bin/env python3
import logging
from src.summarizer.paper_summarizer import PaperSummarizer
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Regenerate markdown summary for a paper')
    parser.add_argument('paper_id', help='The paper ID to regenerate markdown for')
    args = parser.parse_args()
    
    paper_id = args.paper_id
    logger.info(f"Regenerating markdown summary for paper {paper_id}")
    
    # Initialize the summarizer
    summarizer = PaperSummarizer()
    
    # Regenerate the markdown summary
    markdown = summarizer.regenerate_markdown_summary(paper_id)
    
    if markdown:
        logger.info(f"Successfully regenerated markdown summary ({len(markdown)} chars)")
        
        # Verify if Figure 7 is included
        if "Figure 7" in markdown:
            logger.info("Figure 7 reference found in the markdown")
        else:
            logger.warning("Figure 7 reference NOT found in the markdown")
    else:
        logger.error("Failed to regenerate markdown summary")

if __name__ == "__main__":
    main() 