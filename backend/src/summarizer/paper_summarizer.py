import anthropic
from typing import Tuple, List, Optional
import json
from pathlib import Path
import logging
import base64
import re
from backend.src.models.article import Article

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

        prompt = """You are an expert research assistant analyzing a scientific paper. Create a detailed, informative summary with a clear structure following this format:

<FIGURES>
List ONLY the most informative figure/table numbers (max 4-6), one per line
For figures with subfigures, specify:
- Just the number (e.g., "2") to include all subfigures
- Number.letter (e.g., "2.a") for specific subfigures
</FIGURES>

<THUMBNAIL>
Single most visually compelling figure number for thumbnail, optionally with subfigure letter (e.g., "2.a")
</THUMBNAIL>

<SUMMARY>
# Paper Summary

This paper presents [brief 1-sentence description that captures the essence of the paper]. The authors [describe research approach] to address [specific problem or challenge] in the field of [research area]. Their work makes several important contributions:

## Key Contributions
- [3-5 bullet points highlighting the most significant contributions - be specific and technical]

## Problem Statement and Background
[1-2 paragraphs describing the problem addressed and necessary context]

## Methods
[2-3 paragraphs explaining the technical approach, with specific details]

## Results
[2-3 paragraphs on the primary findings]


## Implications and Limitations
[1-2 paragraphs on both the significance of the work and its limitations]

## Related Work and Future Directions
[Paragraph discussing how this work relates to previous research and potential future developments]
</SUMMARY>

Important guidelines:
1. Be comprehensive while maintaining technical precision - each section should provide substantive details
2. Integrate figure references (<FIGURE_ID>X</FIGURE_ID> or <FIGURE_ID>X.a</FIGURE_ID> for subfigures) throughout ALL sections of the summary to create a cohesive narrative
3. For each figure mentioned, provide a thorough explanation (4-5 sentences) directly where the figure is referenced in the text
4. Make sure to describe what the figure shows, its methodology, its significance to the paper's claims, and how it supports the main thesis
5. For the thumbnail, select the figure that best represents the paper's core contribution
6. Use appropriate technical language and explain complex concepts clearly
7. Critically analyze the work, noting both strengths and limitations
8. Ensure the entire summary has a logical flow between sections"""

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
            
            # Log the full response for debugging
            self.logger.info(f"Full response from Claude: {content}")

            # Parse the response using the XML tag structure - use more greedy matching
            summary_match = re.search(r'<SUMMARY>(.*?)</SUMMARY>', content, re.DOTALL)
            figures_match = re.search(r'<FIGURES>(.*?)</FIGURES>', content, re.DOTALL)
            thumbnail_match = re.search(r'<THUMBNAIL>(.*?)</THUMBNAIL>', content, re.DOTALL)
            
            # If the normal match doesn't work, try a more expansive pattern
            if not summary_match:
                # Try matching everything after # Paper Summary
                summary_match = re.search(r'# Paper Summary(.*?)$', content, re.DOTALL)
                
            # Debug - log the first few characters of the matched summary
            if summary_match:
                self.logger.info(f"Summary match first 100 chars: {summary_match.group(1)[:100]}")
                self.logger.info(f"Summary match length: {len(summary_match.group(1))}")
            
            # Debug the regex matches
            self.logger.info(f"Summary match found: {summary_match is not None}")
            self.logger.info(f"Figures match found: {figures_match is not None}")
            self.logger.info(f"Thumbnail match found: {thumbnail_match is not None}")

            summary = summary_match.group(1).strip() if summary_match else ""
            figures = []
            if figures_match:
                # Process figure references, handling both full figures and subfigures
                for fig in figures_match.group(1).split('\n'):
                    fig = fig.strip()
                    if not fig:
                        continue
                        
                    # Handle patterns like "1 - Core methodology visualization..." by extracting just the number
                    dash_match = re.match(r'(\d+)\s*-\s*.*', fig)
                    if dash_match:
                        fig = dash_match.group(1)
                        
                    # Check if it's a subfigure reference (e.g., "2.a")
                    subfig_match = re.match(r'(\d+)\.([a-z])', fig)
                    if subfig_match:
                        figures.append(f"{subfig_match.group(1)}.{subfig_match.group(2)}")
                    elif fig.isdigit():
                        figures.append(fig)

            # Process thumbnail reference
            thumbnail = None
            if thumbnail_match:
                thumb_ref = thumbnail_match.group(1).strip()
                if thumb_ref and thumb_ref.lower() != "none":
                    # Handle both simple figure numbers and subfigure references
                    subfig_match = re.match(r'(\d+)\.([a-z])', thumb_ref)
                    if subfig_match:
                        thumbnail = f"{subfig_match.group(1)}.{subfig_match.group(2)}"
                    elif thumb_ref.isdigit():
                        thumbnail = thumb_ref

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
