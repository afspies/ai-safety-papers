import sys
from pathlib import Path
import logging
import json
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import re

# Add the src directory to the Python path
project_root = Path(__file__).parents[2]
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Now we can import from the src directory
from utils.ar5iv_figure_processor import Ar5ivFigureProcessor
from models.article import Article
from main import clean_latex, create_post_markdown

def setup_test_article() -> Article:
    """Create a test article instance."""
    article = Article(
        "1ac2d6f203b3bdd3503357b0839c24a485d6ce1d",
        "Test Paper",
        "https://arxiv.org/abs/2310.02207"
    )
    
    # Set up test paths
    test_data_dir = Path(__file__).parent / "test_data"
    article.data_folder = test_data_dir / article.uid
    article.data_folder.mkdir(parents=True, exist_ok=True)
    
    # Add dummy abstract to avoid None error
    article.abstract = ""
    article.venue = ""
    article.submitted_date = None
    article.authors = []
    
    return article

def test_latex_parsing():
    """Test LaTeX parsing from ar5iv HTML to markdown."""
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Set up test article
    article = setup_test_article()
    
    # Initialize figure processor
    processor = Ar5ivFigureProcessor()
    
    try:
        # Get ar5iv HTML
        arxiv_html_url = processor._get_ar5iv_url(article.url)
        response = requests.get(arxiv_html_url)
        response.raise_for_status()
        
        # Set base URL for image downloads - ar5iv uses a specific structure
        arxiv_id = arxiv_html_url.split('/')[-1]
        processor.current_base_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"
        logger.debug(f"Set base URL to: {processor.current_base_url}")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Process all figure captions to test LaTeX parsing
        figures_dir = article.data_folder / "figures"
        figures_dir.mkdir(exist_ok=True)
        
        figures = {}
        for i, element in enumerate(soup.find_all(['figure', 'table'])):
            result = processor._process_element(element, i, figures_dir)
            if result:
                fig_id, figure_data = result
                figures[fig_id] = {
                    'path': str(figure_data.path.relative_to(figures_dir)),
                    'caption': figure_data.caption,
                    'type': figure_data.type,
                    'content': figure_data.content
                }
        
        # Save figures metadata
        with open(figures_dir / 'figures_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(figures, f, indent=2, ensure_ascii=False)
        
        # Create a better formatted dummy summary
        dummy_summary = "# Test Summary with Equations\n\n"
        for fig_id, fig_data in figures.items():
            # Add section header for each figure/table
            dummy_summary += f"## {fig_id.replace('_', ' ').title()}\n\n"
            
            # Add caption if it exists
            if fig_data['caption']:
                dummy_summary += f"**Caption:** {fig_data['caption']}\n\n"
            
            # Add content for tables
            if fig_data.get('content'):
                dummy_summary += "**Content:**\n\n"
                dummy_summary += f"{fig_data['content']}\n\n"
            
            # Add figure reference
            dummy_summary += f"<FIGURE_ID>{fig_id.replace('fig', '')}</FIGURE_ID>\n\n"
            
            # Add separator
            dummy_summary += "---\n\n"
        
        # Generate markdown
        markdown = create_post_markdown(article, dummy_summary, {})
        
        # Save output
        output_dir = Path("/Users/alex/Desktop/playground/ai-safety-papers/ai-safety-site/content/en/posts/test")
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / "index.md", 'w', encoding='utf-8') as f:
            f.write(markdown)
            
        logger.info(f"Test output saved to {output_dir / 'index.md'}")
        
        # Print some example equations for verification
        print("\nExample equations from the output:")
        equations = re.findall(r'\$[^$]+\$', markdown)
        for i, eq in enumerate(equations[:5]):  # Print first 5 equations
            print(f"Equation {i+1}: {eq}")
            
    except Exception as e:
        logger.error(f"Error during test: {e}")
        raise

if __name__ == "__main__":
    test_latex_parsing() 