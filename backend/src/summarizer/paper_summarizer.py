import anthropic
from typing import Tuple, List, Optional
import re
import pymupdf
from ..models.article import Article
import json

class PaperSummarizer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def summarize(self, article: Article) -> Tuple[str, List[str], Optional[str]]:
        """
        Summarize the paper and return the summary, list of figures to display, and thumbnail figure.
        
        Args:
            article: An Article instance that has already been parsed
            
        Returns:
            Tuple containing:
            - Summary text with figure placeholders
            - List of figure IDs to display
            - Figure ID to use as thumbnail (or None for default)
        """
        # Get figure information
        figure_captions = []
        for page_num, page in enumerate(article.parsed_doc.pages):
            for fig_num, figure in enumerate(page.images):
                figure_id = f"fig_{page_num}_{fig_num}"
                # Find associated caption
                for caption in page.captions:
                    if caption.text:
                        figure_captions.append((figure_id, caption['text']))
                        break

        # Prepare figure information for Claude
        figures_info = "\n".join([f"Figure {fig_id}: {caption}" 
                                for fig_id, caption in figure_captions])

        # Get text from PDF
        text = article.get_raw_text()

        prompt = f"""You are a research paper summarizer. Please provide a detailed summary of the following paper. 
        The summary should be engaging and accessible to a technical audience.
        
        After analyzing the paper, also indicate which figures (if any) should be included in the summary 
        and which figure would make the best thumbnail.

        Available figures:
        {figures_info}

        Paper text:
        {text[:50000]}  # Truncating to respect context limits

        Please provide your response using the following XML-style tags:
        <SUMMARY>
        Your detailed summary here, use <FIGURE_ID> to indicate where figures should be inserted
        </SUMMARY>
        <FIGURES>
        List of figure IDs to include, one per line
        </FIGURES>
        <THUMBNAIL>
        Single figure ID for thumbnail, or "NONE" if no figure is suitable
        </THUMBNAIL>
        """

        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0.0,
            system="You are a research paper summarizer that creates detailed, technical summaries.",
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse the response using updated regex patterns
        content = response.content[0].text
        summary_match = re.search(r'<SUMMARY>(.*?)</SUMMARY>', content, re.DOTALL)
        figures_match = re.search(r'<FIGURES>(.*?)</FIGURES>', content, re.DOTALL)
        thumbnail_match = re.search(r'<THUMBNAIL>(.*?)</THUMBNAIL>', content, re.DOTALL)

        summary = summary_match.group(1).strip() if summary_match else ""
        figures = [fig.strip() for fig in figures_match.group(1).split('\n')] if figures_match else []
        thumbnail = thumbnail_match.group(1).strip() if thumbnail_match else None
        
        if thumbnail == "NONE":
            thumbnail = None

        return summary, figures, thumbnail
