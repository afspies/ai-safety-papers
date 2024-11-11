import anthropic
from typing import Tuple, List, Optional
import json
from pathlib import Path
import logging
import base64
import re
from models.article import Article

class PaperSummarizer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.logger = logging.getLogger(__name__)

    def summarize(self, article: Article) -> Tuple[str, List[str], Optional[str]]:
        """
        Summarize the paper and return the summary, list of figures to display, and thumbnail figure.
        Checks for existing summary before generating a new one.
        
        Args:
            article: An Article instance with a PDF path set
            
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
                    summary_data.get('thumbnail_figure')
                )
            except Exception as e:
                self.logger.warning(f"Error loading existing summary: {e}. Generating new summary.")

        if not article.pdf_path or not article.pdf_path.exists():
            self.logger.error("PDF path not set or file does not exist")
            raise ValueError("PDF file not available")

        # Read PDF file as base64
        with open(article.pdf_path, 'rb') as f:
            pdf_data = base64.b64encode(f.read()).decode('utf-8')

        prompt = """You are an expert research assistant. Please provide a detailed summary of this paper.
        The summary should be engaging and accessible to a technical audience.
        
        Please also analyze the figures and tables in the paper and indicate which ones are most important 
        for understanding the key points. Suggest which figure would make the best thumbnail image. 
        
        In addition to utilizing markdown syntax for improved text formatting, please provide your response using the following XML-style tags:
        <FIGURES>
        List of figure/table numbers to include, one per line (e.g., "1" for Figure 1)
        </FIGURES>
        <THUMBNAIL>
        Single figure number for thumbnail, or "NONE" if no figure is suitable
        </THUMBNAIL>
        <SUMMARY>
        Your detailed summary here. Use <FIGURE_ID>X</FIGURE_ID> to indicate where Figure X should be inserted.
        </SUMMARY>"""

        try:
            response = self.client.beta.messages.create(
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
                                "data": pdf_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )

            content = response.content[0].text

            # Parse the response using the same XML tag structure
            summary_match = re.search(r'<SUMMARY>(.*?)</SUMMARY>', content, re.DOTALL)
            figures_match = re.search(r'<FIGURES>(.*?)</FIGURES>', content, re.DOTALL)
            thumbnail_match = re.search(r'<THUMBNAIL>(.*?)</THUMBNAIL>', content, re.DOTALL)

            summary = summary_match.group(1).strip() if summary_match else ""
            figures = [fig.strip() for fig in figures_match.group(1).split('\n')] if figures_match else []
            thumbnail = thumbnail_match.group(1).strip() if thumbnail_match else None

            # Filter out empty strings and non-numeric values from figures
            figures = [fig for fig in figures if fig and fig.isdigit()]
            if thumbnail and not thumbnail.isdigit():
                thumbnail = None

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

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            raise
