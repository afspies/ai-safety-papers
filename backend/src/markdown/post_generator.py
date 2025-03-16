import re
import logging
import shutil
from pathlib import Path
from datetime import datetime
import json
from backend.src.models.article import Article
from backend.src.models.post import Post
from backend.src.models.figure import Figure

logger = logging.getLogger(__name__)

def escape_yaml(text: str) -> str:
    """Escape text for YAML frontmatter."""
    if not text:
        return ""
    
    # Only escape quotes and backslashes
    text = text.replace('\\', '\\\\')  # escape backslashes first
    text = text.replace('"', '\\"')    # escape quotes
    
    # Remove any accidental double escapes
    text = text.replace('\\\\\\', '\\\\')
    
    return text

def escape_caption(caption: str) -> str:
    """Escape caption text for Hugo shortcode."""
    if not caption:
        return ""
        
    caption = ' '.join(caption.splitlines())
    caption = re.sub(r'(?<!\\)"', "'", caption)
    caption = caption.replace('\\"', '"').replace('"', '\\"')
    caption = caption.replace('`', '\\`')
    caption = caption.replace('\\', '\\\\')
    caption = caption.replace('$', '\\$')
    
    return caption

def format_caption(elem_id: str, caption_text: str, is_subfigure: bool = False, subfig_id: str = None) -> str:
    """Format caption text with proper figure/table numbering."""
    try:
        # Extract number from elem_id (e.g., "fig2" -> "2", "appendix_tab1" -> "1")
        id_match = re.search(r'(?:appendix_)?(?:fig|tab)(\d+)', elem_id)
        number = id_match.group(1) if id_match else ""
        
        if is_subfigure:
            # For subfigures, just return the letter label
            return f"({subfig_id})"
        else:
            # For main figures/tables
            is_appendix = elem_id.startswith('appendix_')
            is_table = elem_id.startswith(('tab', 'appendix_tab'))
            
            prefix = "Table" if is_table else "Figure"
            if is_appendix:
                number = f"A{number}"
            
            # Only add the prefix if there's a caption
            if caption_text:
                return f"**{prefix} {number}:** {caption_text}"
            return caption_text
            
    except Exception as e:
        logger.warning(f"Error formatting caption: {e}")
        return caption_text

def create_post_markdown(post: Post) -> str:
    """
    Generate markdown content for the post, handling subfigures with improved formatting.
    
    Args:
        post: Post object containing article, summary, and figures
    
    Returns:
        Markdown string for the post
    """
    article = post.article
    summary = post.summary
    post_dir = post.post_dir
    
    # Format frontmatter
    author_list = article.authors if isinstance(article.authors, list) else []
    quoted_authors = [f'"{author.strip()}"' for author in author_list]
    description = article.abstract[:200] + "..." if hasattr(article, 'abstract') and len(article.abstract) > 200 else article.abstract if hasattr(article, 'abstract') else ''
    abstract = article.abstract if hasattr(article, 'abstract') else ''
    tldr = article.tldr if hasattr(article, 'tldr') and article.tldr else ''
    
    # Additional metadata for improved display
    venue = article.venue if hasattr(article, 'venue') and article.venue else ''
    publication_date = article.submitted_date.strftime('%B %d, %Y') if hasattr(article, 'submitted_date') and article.submitted_date else 'Unknown'
    
    # Define tags if available
    tags = []
    if hasattr(article, 'tags') and article.tags:
        tags = article.tags if isinstance(article.tags, list) else [article.tags]
    
    # Format tags for YAML
    tags_yaml = ""
    if tags:
        tags_yaml = "tags: [" + ", ".join([f'"{tag.strip()}"' for tag in tags]) + "]\n"

    frontmatter = f"""---
title: "{escape_yaml(article.title)}"
description: "{escape_yaml(description)}"
authors: [{', '.join(quoted_authors)}]
date: {datetime.now().strftime('%Y-%m-%d')}
publication_date: {article.submitted_date.strftime('%Y-%m-%d') if hasattr(article, 'submitted_date') and article.submitted_date else 'Unknown'}
venue: "{escape_yaml(venue)}"
paper_url: "{article.url}"
abstract: "{escape_yaml(abstract)}"
tldr: "{escape_yaml(tldr)}"
added_date: {datetime.now().strftime('%Y-%m-%d')}
bookcase_cover_src: '/posts/paper_{article.uid}/thumbnail.png'
{tags_yaml}math: true
katex: true
weight: 1
---

"""

    # Metadata section for better display in the post
    metadata_section = f"""<div class="paper-meta">
  <div class="paper-meta-item">
    <span class="paper-meta-label">Authors:</span>
    <div class="paper-authors">
      {', '.join(author_list)}
    </div>
  </div>
  <div class="paper-meta-item">
    <span class="paper-meta-label">Published:</span>
    <span>{publication_date}</span>
  </div>
"""

    # Add venue if available
    if venue:
        metadata_section += f"""  <div class="paper-meta-item">
    <span class="paper-meta-label">Venue:</span>
    <span>{venue}</span>
  </div>
"""

    # Add original paper link
    metadata_section += f"""  <div class="paper-meta-item">
    <span class="paper-meta-label">Original Paper:</span>
    <a href="{article.url}" target="_blank" rel="noopener">View Paper</a>
  </div>
</div>

"""
    
    # Main content - ensure proper spacing and formatting (don't add Paper Summary twice)
    if summary.startswith("# Paper Summary"):
        content_section = f"""

{summary}"""
    else:
        content_section = f"""

# Paper Summary

{summary}"""
    
    # Combine all sections
    full_content = frontmatter + metadata_section + content_section
    
    # Keep track of figures we've already processed
    processed_figures = set()
    
    # Process figure references in the text - handle XML tags
    figure_pattern = r'<FIGURE_ID>(\d+)(\.([a-z]))?\</FIGURE_ID>'
    
    # After processing tagged references, look for plain figure references like "Figure 19"
    plain_figure_pattern = r'(?<!<)Figure (\d+)(?!\.\d)'
    
    for match in re.finditer(figure_pattern, full_content):
        full_match = match.group(0)
        fig_num = match.group(1)
        subfig_letter = match.group(3)  # Will be None for main figures
        
        # Track which figures we've processed
        fig_key = f"{fig_num}"
        if subfig_letter:
            fig_key += f".{subfig_letter}"
            
        if fig_key in processed_figures:
            # If we've already processed this figure, just replace the tag
            replacement = f"Figure {fig_num}"
            if subfig_letter:
                replacement += f".{subfig_letter}"
            full_content = full_content.replace(full_match, replacement)
            continue
            
        processed_figures.add(fig_key)
        
        fig_id = f"fig{fig_num}"
        
        # Get figure from post's figures dictionary
        figure = post.get_figure(fig_id)
        
        if figure:
            if figure.has_subfigures:
                if subfig_letter:
                    # Handle specific subfigure reference with improved formatting
                    subfig_data = next((s for s in figure.subfigures if s['id'] == subfig_letter), None)
                    if subfig_data:
                        subfig_id = f"{fig_id}_{subfig_letter}"
                        # Generate subfigure shortcode with formatted caption
                        formatted_caption = format_caption(fig_id, subfig_data['caption'], True, subfig_letter)
                        replacement = f"""

{{{{< figure src="{subfig_id}.png" caption="{escape_caption(formatted_caption)}" >}}}}

"""
                    else:
                        logger.warning(f"Subfigure {subfig_letter} not found in {fig_id}")
                        replacement = f"Figure {fig_num}({subfig_letter})"
                else:
                    # Handle main figure with subfigures using subfigures shortcode
                    subfigs_content = []
                    for subfig in figure.subfigures:
                        subfig_id = f"{fig_id}_{subfig['id']}"
                        formatted_caption = format_caption(fig_id, subfig['caption'], True, subfig['id'])
                        subfigs_content.append(
                            f'{{{{< subfigure src="{subfig_id}.png" caption="{escape_caption(formatted_caption)}" >}}}}'
                        )
                    
                    formatted_main_caption = format_caption(fig_id, figure.caption)
                    replacement = f"""

{{{{< subfigures caption="{escape_caption(formatted_main_caption)}" >}}}}
{''.join(subfigs_content)}
{{{{< /subfigures >}}}}

"""
            else:
                # Handle regular figure with improved formatting
                formatted_caption = format_caption(fig_id, figure.caption)
                replacement = f"""

{{{{< figure src="{fig_id}.png" caption="{escape_caption(formatted_caption)}" >}}}}

"""
        else:
            logger.warning(f"Figure {fig_id} not found in post figures")
            replacement = f"Figure {fig_num}"
        
        full_content = full_content.replace(full_match, replacement)
    
    # Now process plain figure references (Figure N) after processing XML tags
    for match in re.finditer(plain_figure_pattern, full_content):
        full_match = match.group(0)
        fig_num = match.group(1)
        
        # Skip if we've already processed this figure
        fig_key = f"{fig_num}"
        if fig_key in processed_figures:
            continue
            
        processed_figures.add(fig_key)
        
        fig_id = f"fig{fig_num}"
        
        # Get figure from post's figures dictionary
        figure = post.get_figure(fig_id)
        
        if figure:
            # Handle regular figure
            formatted_caption = format_caption(fig_id, figure.caption)
            replacement = f"""

{{{{< figure src="{fig_id}.png" caption="{escape_caption(formatted_caption)}" >}}}}

{full_match}"""
            full_content = full_content.replace(full_match, replacement)
        else:
            logger.warning(f"Figure {fig_id} not found in post figures")
    
    # Clean up any multiple consecutive blank lines
    full_content = re.sub(r'\n{3,}', '\n\n', full_content)
    
    # Ensure proper spacing between sections (numbered points)
    full_content = re.sub(r'(\d+\.) ', r'\n\n\1 ', full_content)
    
    return full_content

def save_post_markdown(post: Post) -> Path:
    """
    Generate markdown for a post and save it to the post directory.
    
    Args:
        post: Post object to generate markdown for
        
    Returns:
        Path to the saved markdown file
    """
    # Make sure post directory exists
    post_dir = post.post_dir
    post_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate markdown
    markdown = create_post_markdown(post)
    
    # Save markdown
    index_path = post_dir / "index.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    # Process display figures
    post.process_display_figures()
    
    # Set thumbnail
    post.set_thumbnail()
    
    return index_path