import anthropic
from typing import Tuple, List, Optional
import re
import pymupdf
from models.article import Article
import json
from pathlib import Path
import logging

class PaperSummarizer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.logger = logging.getLogger(__name__)

    def summarize(self, article: Article) -> Tuple[str, List[str], Optional[str]]:
        """
        Summarize the paper and return the summary, list of figures to display, and thumbnail figure.
        Checks for existing summary before generating a new one.
        
        Args:
            article: An Article instance that has already been parsed
            
        Returns:
            Tuple containing:
            - Summary text with figure placeholders
            - List of figure IDs to display
            - Figure ID to use as thumbnail (or None for default)
        """
        # Check for existing summary
        summary_path = article.data_folder / "summary.json"
        if summary_path.exists():
            self.logger.info(f"Found existing summary for article {article.uid}")
            try:
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)
                return (
                    summary_data['summary'],
                    summary_data['display_figures'],
                    summary_data.get('thumbnail_figure')  # Use get() in case older summaries don't have this field
                )
            except Exception as e:
                self.logger.warning(f"Error loading existing summary: {e}. Generating new summary.")

        # Get figure information
        self.logger.debug(f"Beginning figure extraction for article {article.uid}")
        figure_captions = []
        
        if not hasattr(article.parsed_doc, 'pages'):
            self.logger.warning(f"No pages found in parsed document for article {article.uid}")
            return self._generate_summary_without_figures(article)
        
        for page_num, page in enumerate(article.parsed_doc.pages):
            self.logger.debug(f"Processing page {page_num}, found {len(page.images)} images")
            for fig_num, figure in enumerate(page.images):
                figure_id = f"fig_{page_num}_{fig_num}"
                self.logger.debug(f"Processing figure {figure_id}")
                
                # Find associated caption
                caption_found = False
                for caption in page.captions:
                    if caption.text:
                        figure_captions.append((figure_id, caption['text']))
                        caption_found = True
                        self.logger.debug(f"Found caption for {figure_id}: {caption['text'][:100]}...")
                        break
                
                if not caption_found:
                    self.logger.debug(f"No caption found for {figure_id}")

        if not figure_captions:
            self.logger.warning(f"No figures with captions found in article {article.uid}")
            return self._generate_summary_without_figures(article)

        # Prepare figure information for Claude
        figures_info = "\n".join([f"Figure {fig_id}: {caption}" 
                                for fig_id, caption in figure_captions])
        
        self.logger.debug(f"Prepared {len(figure_captions)} figures for summarization")

        # Get text from PDF
        text = article.get_raw_text()

        prompt = f"""You are an expert research assistant. You are tasked with summarizing papers. Please provide a detailed summary of the following paper. 
        The summary should be engaging and accessible to a technical audience.
        
        As well as analyzing the paper, also indicate which figures should be included in the summary. It is OK if you don't think there are any salient figures or tables.
        and which figure would make the best thumbnail. If you wish to include mathematical formulas in your summary, please do so using standard latex formatting.

        Available figures:
        {figures_info}

        Paper text:
        {text[:50000]}  # Truncating to respect context limits

        Please provide your response using the following XML-style tags:
        <FIGURES>
        List of figure IDs to include, one per line
        </FIGURES>
        <THUMBNAIL>
        Single figure ID for thumbnail, or "NONE" if no figure is suitable
        </THUMBNAIL>
        <SUMMARY>
        Your detailed summary here, use <FIGURE_ID> to indicate where figures should be inserted
        </SUMMARY>
        """

        response = self.client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=8192,
            temperature=0.0,
            system="You are a research paper summarizer that creates detailed, technical summaries.",
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse the response
        content = response.content[0].text
        summary_match = re.search(r'<SUMMARY>(.*?)</SUMMARY>', content, re.DOTALL)
        figures_match = re.search(r'<FIGURES>(.*?)</FIGURES>', content, re.DOTALL)
        thumbnail_match = re.search(r'<THUMBNAIL>(.*?)</THUMBNAIL>', content, re.DOTALL)

        summary = summary_match.group(1).strip() if summary_match else ""
        figures = [fig.strip() for fig in figures_match.group(1).split('\n')] if figures_match else []
        thumbnail = thumbnail_match.group(1).strip() if thumbnail_match else None
        
        # Validate that suggested figures actually exist
        available_figure_ids = [fig_id for fig_id, _ in figure_captions]
        figures = [fig for fig in figures if fig in available_figure_ids]
        if thumbnail not in available_figure_ids:
            thumbnail = None
        
        self.logger.debug(f"LLM suggested figures: {figures}")
        self.logger.debug(f"LLM suggested thumbnail: {thumbnail}")

        # Save the summary data
        summary_data = {
            'summary': summary,
            'display_figures': figures,
            'thumbnail_figure': thumbnail
        }
        
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved summary for article {article.uid}")
        except Exception as e:
            self.logger.error(f"Error saving summary: {e}")

        return summary, figures, thumbnail

    def _generate_summary_without_figures(self, article: Article) -> Tuple[str, List[str], Optional[str]]:
        """Generate a summary when no figures are available."""
        self.logger.info(f"Generating summary without figures for article {article.uid}")
        
        text = article.get_raw_text()
        
        prompt = f"""You are a research paper summarizer. Please provide a detailed summary of the following paper. 
        The summary should be engaging and accessible to a technical audience.

        Paper text:
        {text[:50000]}  # Truncating to respect context limits

        Please provide your response using the following XML-style tags:
        <SUMMARY>
        Your detailed summary here
        </SUMMARY>
        """

        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0.0,
            system="You are a research paper summarizer that creates detailed, technical summaries.",
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text
        summary_match = re.search(r'<SUMMARY>(.*?)</SUMMARY>', content, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else ""

        # Save the summary data
        summary_data = {
            'summary': summary,
            'display_figures': [],
            'thumbnail_figure': None
        }
        
        try:
            summary_path = article.data_folder / "summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved summary without figures for article {article.uid}")
        except Exception as e:
            self.logger.error(f"Error saving summary: {e}")

        return summary, [], None
