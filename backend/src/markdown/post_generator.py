import re
import logging
import shutil
from pathlib import Path
from datetime import datetime
import json
from models.article import Article

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

def create_post_markdown(article: Article, summary: str, post_dir: Path) -> str:
    """Generate markdown content for the post, handling subfigures."""
    
    # Format frontmatter
    author_list = article.authors if isinstance(article.authors, list) else []
    quoted_authors = [f'"{author.strip()}"' for author in author_list]
    description = article.abstract[:200] if hasattr(article, 'abstract') else ''
    abstract = article.abstract if hasattr(article, 'abstract') else ''
    tldr = article.tldr if hasattr(article, 'tldr') and article.tldr else ''

    frontmatter = f"""---
title: "{escape_yaml(article.title)}"
description: "{escape_yaml(description)}"
authors: [{', '.join(quoted_authors)}]
date: {datetime.now().strftime('%Y-%m-%d')}
publication_date: {article.submitted_date.strftime('%Y-%m-%d') if hasattr(article, 'submitted_date') and article.submitted_date else 'Unknown'}
venue: "{escape_yaml(article.venue if hasattr(article, 'venue') else '')}"
paper_url: "{article.url}"
abstract: "{escape_yaml(abstract)}"
tldr: "{escape_yaml(tldr)}"
added_date: {datetime.now().strftime('%Y-%m-%d')}
bookcase_cover_src: '/posts/paper_{article.uid}/thumbnail.png'
math: true
katex: true
weight: 1
---

# Summary

"""
    
    content = summary
    
    # Load figure metadata
    figures_metadata = {}
    metadata_path = article.data_folder / "figures" / "figures_metadata.json"
    try:
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                figures_metadata = json.load(f)
            logger.debug(f"Loaded figures metadata from {metadata_path}")
        else:
            logger.warning(f"No figures metadata found at {metadata_path}")
    except Exception as e:
        logger.error(f"Error loading figures metadata: {e}")
    
    # Process figure references in the text
    figure_pattern = r'<FIGURE_ID>(\d+)(\.([a-z]))?\</FIGURE_ID>'
    
    for match in re.finditer(figure_pattern, content):
        full_match = match.group(0)
        fig_num = match.group(1)
        subfig_letter = match.group(3)  # Will be None for main figures
        
        fig_id = f"fig{fig_num}"
        
        if fig_id in figures_metadata:
            metadata = figures_metadata[fig_id]
            
            if metadata.get('type') == 'figure':
                if metadata.get('subfigures'):
                    if subfig_letter:
                        # Handle specific subfigure reference
                        subfig_data = next((s for s in metadata['subfigures'] if s['id'] == subfig_letter), None)
                        if subfig_data:
                            subfig_id = f"{fig_id}_{subfig_letter}"
                            # Copy subfigure to post directory
                            shutil.copy2(
                                article.data_folder / "figures" / f"{subfig_id}.png",
                                post_dir / f"{subfig_id}.png"
                            )
                            # Generate subfigure shortcode with formatted caption
                            formatted_caption = format_caption(fig_id, subfig_data['caption'], True, subfig_letter)
                            replacement = f"""
{{{{< figure src="{subfig_id}.png" caption="{escape_caption(formatted_caption)}" >}}}}
Figure {fig_num}({subfig_letter})"""
                        else:
                            logger.warning(f"Subfigure {subfig_letter} not found in {fig_id}")
                            replacement = f"Figure {fig_num}({subfig_letter})"
                    else:
                        # Handle main figure with subfigures using subfigures shortcode
                        subfigs_content = []
                        for subfig in metadata['subfigures']:
                            subfig_id = f"{fig_id}_{subfig['id']}"
                            # Copy subfigure to post directory
                            shutil.copy2(
                                article.data_folder / "figures" / f"{subfig_id}.png",
                                post_dir / f"{subfig_id}.png"
                            )
                            formatted_caption = format_caption(fig_id, subfig['caption'], True, subfig['id'])
                            subfigs_content.append(
                                f'{{{{< subfigure src="{subfig_id}.png" caption="{escape_caption(formatted_caption)}" >}}}}'
                            )
                        
                        formatted_main_caption = format_caption(fig_id, metadata['caption'])
                        replacement = f"""
{{{{< subfigures caption="{escape_caption(formatted_main_caption)}" >}}}}
{''.join(subfigs_content)}
{{{{< /subfigures >}}}}
Figure {fig_num}"""
                else:
                    # Handle regular figure
                    # Copy figure to post directory
                    shutil.copy2(
                        article.data_folder / "figures" / f"{fig_id}.png",
                        post_dir / f"{fig_id}.png"
                    )
                    formatted_caption = format_caption(fig_id, metadata['caption'])
                    replacement = f"""
{{{{< figure src="{fig_id}.png" caption="{escape_caption(formatted_caption)}" >}}}}
Figure {fig_num}"""
            else:
                # Handle table references with formatted caption
                formatted_caption = format_caption(fig_id, metadata['caption'])
                replacement = f"""
{metadata.get('content', '')}
{formatted_caption}
Table {fig_num}"""
        else:
            logger.warning(f"Figure {fig_id} not found in metadata")
            replacement = f"Figure {fig_num}"
        
        content = content.replace(full_match, replacement)
    
    # Clean up any multiple consecutive blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Ensure proper spacing between sections (numbered points)
    content = re.sub(r'(\d+\.) ', r'\n\n\1 ', content)
    
    return frontmatter + content 