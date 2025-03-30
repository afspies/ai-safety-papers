#!/usr/bin/env python3
import os
import sys
import logging
import tempfile
from pathlib import Path
import requests
import hashlib
from urllib.parse import urlparse
import re

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from backend.src.models.article import Article
from backend.src.models.post import Post
from backend.src.utils.figure_extractor_manager import FigureExtractorManager
from backend.src.markdown.post_generator import save_post_markdown
from backend.src.summarizer.paper_summarizer import PaperSummarizer
# from backend.src.utils.config_loader import load_config

def load_config():
    """Load config from secrets directory."""
    import yaml
    with open(os.path.join(project_root, "secrets", "config.yaml"), "r") as f:
        return yaml.safe_load(f)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_pdf(url: str, output_path: Path) -> Path:
    """Download a PDF from a URL."""
    logger.info(f"Downloading PDF from {url}")
    
    # If it's an arXiv URL, convert to PDF URL
    if 'arxiv.org/abs' in url:
        paper_id = url.split('/')[-1]
        url = f"https://arxiv.org/pdf/{paper_id}.pdf"
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return output_path

def hash_url(url: str) -> str:
    """Create a SHA-1 hash of a URL for use as a unique ID."""
    return hashlib.sha1(url.encode()).hexdigest()

def get_paper_info(paper_url: str) -> dict:
    """Get basic paper info from arXiv API."""
    # Extract paper ID from URL
    paper_id = None
    if 'arxiv.org' in paper_url:
        match = re.search(r'(?:arxiv.org/(?:abs|pdf)/)?([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)', paper_url)
        if match:
            paper_id = match.group(1)
    
    if not paper_id:
        logger.warning(f"Could not extract arXiv ID from URL: {paper_url}")
        return {
            'title': 'Unknown Paper',
            'authors': ['Unknown Author'],
            'abstract': 'No abstract available',
            'url': paper_url
        }
    
    # Query arXiv API
    api_url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
    response = requests.get(api_url)
    response.raise_for_status()
    
    # Parse XML response
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response.content)
    
    # Get paper info
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    entry = root.find('.//atom:entry', ns)
    
    if entry is None:
        logger.warning(f"No paper found with ID: {paper_id}")
        return {
            'title': 'Unknown Paper',
            'authors': ['Unknown Author'],
            'abstract': 'No abstract available',
            'url': paper_url
        }
    
    title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
    
    authors = []
    for author_elem in entry.findall('.//atom:author/atom:name', ns):
        authors.append(author_elem.text.strip())
    
    abstract = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
    
    return {
        'title': title,
        'authors': authors,
        'abstract': abstract,
        'url': paper_url
    }

def process_paper(paper_url: str, output_dir: Path) -> Path:
    """Process a paper and create a post."""
    # Generate a unique ID for the paper
    paper_uid = hash_url(paper_url)
    logger.info(f"Processing paper: {paper_url} (ID: {paper_uid})")
    
    # Create data directory
    data_dir = output_dir / "data" / paper_uid
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create directory for figures
    figures_dir = data_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    
    # Download PDF
    pdf_path = data_dir / f"{paper_uid}.pdf"
    if not pdf_path.exists():
        download_pdf(paper_url, pdf_path)
    
    # Save arXiv ID to a file for ar5iv extractor
    arxiv_id_path = data_dir / "arxiv_id.txt"
    parsed_url = urlparse(paper_url)
    arxiv_id = os.path.basename(parsed_url.path)
    with open(arxiv_id_path, 'w') as f:
        f.write(arxiv_id)
    
    # Get paper info
    paper_info = get_paper_info(paper_url)
    logger.info(f"Paper info: {paper_info['title']} by {', '.join(paper_info['authors'])}")
    
    # Create article object
    article = Article(
        uid=paper_uid,
        title=paper_info['title'],
        authors=paper_info['authors'],
        abstract=paper_info['abstract'],
        url=paper_url,
        pdf_path=pdf_path,
        data_folder=data_dir,
        website_content_path=output_dir / "ai-safety-site/content/en"
    )
    
    # Use PaperSummarizer to generate summary
    config = load_config()
    if "anthropic" in config and "api_key" in config["anthropic"]:
        api_key = config["anthropic"]["api_key"]
        logger.info("Using Anthropic API to generate summary")
        summarizer = PaperSummarizer(api_key)
        
        try:
            summary, display_figures, thumbnail = summarizer.summarize(article)
            logger.info(f"Successfully generated summary with {len(display_figures)} display figures")
            logger.info(f"Summary length: {len(summary)} characters")
            logger.info(f"Summary excerpt: {summary[:300]}...")
            
            # Save the summary directly to ensure it's being saved correctly
            with open(article.data_folder / "summary_direct.txt", "w", encoding="utf-8") as f:
                f.write(summary)
                
            # Also save the full response for debugging
            try:
                # Get the response directly from Claude
                client = anthropic.Anthropic(api_key=api_key)
                response = client.beta.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    betas=["pdfs-2024-09-25"],
                    max_tokens=4096,
                    temperature=0,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": base64.b64encode(open(article.pdf_path, 'rb').read()).decode('utf-8')
                                }
                            },
                            {
                                "type": "text",
                                "text": summarizer.prompt
                            }
                        ]
                    }]
                )
                content = response.content[0].text
                with open(article.data_folder / "claude_full_response.txt", "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error saving Claude response: {e}")
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}", exc_info=True)
            # Fallback to dummy summary
            summary = f"""This paper discusses {paper_info['title']}.

The authors propose a novel approach to address important challenges in the field.

<FIGURE_ID>1</FIGURE_ID> shows the main architecture of their proposed method.

Their experiments demonstrate significant improvements over previous approaches as shown in <FIGURE_ID>2</FIGURE_ID>.
"""
            display_figures = ["fig1", "fig2"]
            thumbnail = "fig1"
    else:
        logger.warning("Anthropic API key not found, using dummy summary")
        summary = f"""This paper discusses {paper_info['title']}.

The authors propose a novel approach to address important challenges in the field.

<FIGURE_ID>1</FIGURE_ID> shows the main architecture of their proposed method.

Their experiments demonstrate significant improvements over previous approaches as shown in <FIGURE_ID>2</FIGURE_ID>.
"""
        display_figures = ["fig1", "fig2"]
        thumbnail = "fig1"
    
    # Create post object with the generated summary
    post = Post(
        article=article,
        summary=summary
    )
    
    # Extract figures using the manager
    extractor_manager = FigureExtractorManager()
    success = extractor_manager.extract_figures(post, arxiv_id_path, pdf_path, force=True)
    
    if not success:
        logger.warning("Figure extraction failed")
    
    # Set display figures from the Claude-generated list
    if "anthropic" in config and "api_key" in config["anthropic"] and post.figures:
        # Convert figure numbers to figure IDs
        filtered_display_figures = []
        for fig_num in display_figures:
            # Handle typical figure numbers like "1" or "1.a"
            if "." in fig_num:
                num, subfig = fig_num.split(".")
                fig_id = f"fig{num}"
                if fig_id in post.figures and post.figures[fig_id].has_subfigures:
                    filtered_display_figures.append(fig_id)
            else:
                fig_id = f"fig{fig_num}"
                if fig_id in post.figures:
                    filtered_display_figures.append(fig_id)
        
        # If we have display figures, use them
        if filtered_display_figures:
            post.display_figures = filtered_display_figures
        else:
            # Fallback to first 3 figures
            post.display_figures = list(post.figures.keys())[:3]
        
        # Set thumbnail
        if thumbnail:
            thumb_id = f"fig{thumbnail}"
            if thumb_id in post.figures:
                post.thumbnail_figure = thumb_id
            else:
                post.thumbnail_figure = post.display_figures[0] if post.display_figures else None
        else:
            post.thumbnail_figure = post.display_figures[0] if post.display_figures else None
    # Fallback to first 3 figures if we don't have a Claude summary
    elif post.figures:
        post.display_figures = list(post.figures.keys())[:3]
        post.thumbnail_figure = post.display_figures[0] if post.display_figures else None
    
    # Generate and save markdown
    post_path = save_post_markdown(post)
    logger.info(f"Post saved to {post_path}")
    
    return post_path

def main():
    # Load config
    config = load_config()
    
    # Create output directory
    output_dir = Path(project_root)
    
    # Process a sample paper
    paper_url = "https://arxiv.org/abs/2202.05262"  # "ViT: Vision Transformer" - should have many figures
    
    try:
        post_path = process_paper(paper_url, output_dir)
        logger.info(f"Successfully processed paper. Post saved to {post_path}")
    except Exception as e:
        logger.error(f"Error processing paper: {e}", exc_info=True)

if __name__ == "__main__":
    main()