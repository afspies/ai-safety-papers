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

def process_figure_references(markdown: str, post: Post) -> str:
    """
    Process all figure references in markdown and append figure markdown.
    
    Args:
        markdown: The input markdown text
        post: Post object containing the figures data
        
    Returns:
        Processed markdown with figure shortcodes added
    """
    # Split markdown into lines for processing
    lines = markdown.splitlines()
    processed_lines = []
    processed_figures = set()
    
    # Figure reference pattern - updated to handle both uppercase and lowercase subfigure letters
    figure_pattern = r'<FIGURE_ID>(\d+)(\.([a-zA-Z]))?\</FIGURE_ID>'
    
    for line in lines:
        processed_lines.append(line)
        
        # Find all figure references in this line
        matches = list(re.finditer(figure_pattern, line))
        
        if not matches:
            continue
            
        figure_markdown_lines = []
        
        # Process each match and add figure markdown
        for match in matches:
            full_match = match.group(0)
            fig_num = match.group(1)
            subfig_letter = match.group(3)  # Will be None for main figures
            
            # Log the detected reference for debugging
            logger.info(f"Found figure reference: {full_match} (fig_num={fig_num}, subfig_letter={subfig_letter})")
            
            # Normalize subfigure letter to lowercase for internal processing
            subfig_letter_normalized = subfig_letter.lower() if subfig_letter else None
            
            # Create a key for tracking processed figures
            fig_key = f"{fig_num}"
            if subfig_letter_normalized:
                fig_key += f".{subfig_letter_normalized}"
                
            # Skip if we've already processed this figure
            if fig_key in processed_figures:
                logger.info(f"Skipping already processed figure: {fig_key}")
                continue
                
            processed_figures.add(fig_key)
            
            # Generate and add figure markdown
            fig_id = f"fig{fig_num}"
            figure = post.get_figure(fig_id)
            
            if figure:
                logger.info(f"Found figure object for {fig_id}")
                if subfig_letter and figure.has_subfigures:
                    logger.info(f"Figure has subfigures: {[s['id'] for s in figure.subfigures]}")
                
                # Generate figure markdown based on type
                figure_markdown = generate_figure_markdown(figure, fig_id, subfig_letter_normalized)
                if figure_markdown:
                    figure_markdown_lines.append(figure_markdown)
                else:
                    logger.warning(f"Failed to generate markdown for {fig_id}{'.'+subfig_letter if subfig_letter else ''}")
            else:
                logger.warning(f"Figure {fig_id} not found in post figures")
        
        # Add all figures for this line with line breaks
        if figure_markdown_lines:
            processed_lines.append("")  # Add empty line before figures
            processed_lines.extend(figure_markdown_lines)
            processed_lines.append("")  # Add empty line after figures
    
    # Replace the figure references with text references
    result = "\n".join(processed_lines)
    
    # Replace references with plain text - updated to handle both uppercase and lowercase
    result = re.sub(r'<FIGURE_ID>(\d+)(\.([a-zA-Z]))?\</FIGURE_ID>', lambda m: 
                  f"Figure {m.group(1)}" + (f".{m.group(3)}" if m.group(3) else ""), 
                  result)
    
    return result

def generate_figure_markdown(figure: Figure, fig_id: str, subfig_letter: str = None) -> str:
    """Generate markdown for a figure or subfigure."""
    if not figure:
        return ""
        
    if subfig_letter:
        # Handle specific subfigure
        # Try to find the subfigure regardless of case
        subfig_data = None
        for subfig in figure.subfigures:
            if subfig['id'].lower() == subfig_letter.lower():
                subfig_data = subfig
                break
                
        if subfig_data:
            subfig_id = f"{fig_id}_{subfig_data['id']}"  # Use original ID from data
            formatted_caption = format_caption(fig_id, subfig_data['caption'], True, subfig_data['id'])
            return f'{{{{< figure src="{subfig_id}.png" caption="{escape_caption(formatted_caption)}" >}}}}'
        else:
            logger.warning(f"Subfigure {subfig_letter} not found in {fig_id} subfigures: {[s['id'] for s in figure.subfigures if 'id' in s]}")
            return ""
        
    # Handle main figure (with or without subfigures)
    if figure.has_subfigures:
        # Generate subfigures shortcode
        subfigs_content = []
        for subfig in figure.subfigures:
            if 'id' not in subfig:
                logger.warning(f"Subfigure in {fig_id} missing 'id' field: {subfig}")
                continue
                
            subfig_id = f"{fig_id}_{subfig['id']}"
            formatted_caption = format_caption(fig_id, subfig['caption'], True, subfig['id'])
            subfigs_content.append(
                f'{{{{< subfigure src="{subfig_id}.png" caption="{escape_caption(formatted_caption)}" >}}}}'
            )
        
        formatted_main_caption = format_caption(fig_id, figure.caption)
        return f"""{{{{< subfigures caption="{escape_caption(formatted_main_caption)}" >}}}}
{''.join(subfigs_content)}
{{{{< /subfigures >}}}}"""
    else:
        # Regular figure
        formatted_caption = format_caption(fig_id, figure.caption)
        return f'{{{{< figure src="{fig_id}.png" caption="{escape_caption(formatted_caption)}" >}}}}'

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
        
    # Add highlight status
    highlight = hasattr(article, 'highlight') and article.highlight

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
highlight: {str(highlight).lower()}
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
    
    # Process figure references - use the new standalone function
    full_content = process_figure_references(full_content, post)
    
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