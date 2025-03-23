from typing import Tuple, List, Optional, Dict, Any
import json
from pathlib import Path
import logging
import base64
import re
from src.models.article import Article
from src.models.supabase import SupabaseDB
from .prompt import summarization_prompt
import dotenv
import os
from litellm import completion

dotenv.load_dotenv()

class PaperSummarizer:
    def __init__(self, model_endpoint:str = "anthropic/claude-3-7-sonnet-latest",  db: Optional[SupabaseDB] = None):
        self.model_endpoint = model_endpoint
        self.logger = logging.getLogger(__name__)
        self.db = db

    def summarize(self, article: Article, ignore_existing_summary: bool = False) -> Tuple[str, List[str], Optional[str]]:
        """
        Summarize the paper and return the summary, list of figures to display, and thumbnail figure.
        Checks for existing summary in Supabase before generating a new one.
        
        Args:
            article: An Article instance with a PDF path set
            
        Returns:
            Tuple containing:
            - Summary text with figure placeholders
            - List of figure IDs to display
            - Figure ID to use as thumbnail (or None for default)
        """
        # Check for existing summary in Supabase first
        if self.db is None:
            self.db = SupabaseDB()
        if not ignore_existing_summary:
            summary_data = self.db.get_summary(article.uid)
            if summary_data:
                self.logger.info(f"Found existing summary in Supabase for article {article.uid}")
                return (
                    summary_data['summary'],
                    summary_data['display_figures'],
                    summary_data.get('thumbnail_figure')
                )
                
            # Check for existing summary in local storage
            summary_path = article.data_folder / "summary.json"
            if summary_path.exists():
                self.logger.info(f"Found existing summary in local storage for article {article.uid}")
                try:
                    with open(summary_path, 'r', encoding='utf-8') as f:
                        summary_data = json.load(f)
                        
                    # Store in Supabase for future use
                    try:
                        self.db.add_summary(
                            article.uid, 
                            summary_data['summary'], 
                            summary_data['display_figures'], 
                            summary_data.get('thumbnail_figure')
                        )
                        self.logger.info(f"Migrated local summary to Supabase for article {article.uid}")
                    except Exception as e:
                        self.logger.warning(f"Error migrating summary to Supabase: {e}")
                        
                    return (
                        summary_data['summary'],
                        summary_data['display_figures'],
                        summary_data.get('thumbnail_figure')
                    )
                except Exception as e:
                    self.logger.warning(f"Error loading existing summary: {e}. Generating new summary.")

        # Production mode - continue with actual API call
        if not article.pdf_path or not article.pdf_path.exists():
            self.logger.error("PDF path not set or file does not exist")
            raise ValueError("PDF file not available")

        # Read PDF file as base64
        with open(article.pdf_path, 'rb') as f:
            pdf_data = base64.b64encode(f.read()).decode('utf-8')

        try:
            # Replace OpenAI API call with LiteLLM completion
            response = completion(
                model=self.model_endpoint,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            { # Prompt
                                "type": "text",
                                "text": summarization_prompt,
                                # "cache_control": {"type": "ephemeral"},
                            },
                            { # PDF file
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data

                                },
                                "citations": {"enabled": True},
                                "context": "The PDF of the paper you should summarize."
                            }
                        ] 
                    }
                ],
            )

            # Extract content from the response (adjusted for LiteLLM response format)
            content = response.choices[0].message.content
            
            # Log the full response for debugging
            self.logger.info(f"Full response from LiteLLM: {content}")

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

            # Save to local storage as backup
            try:
                with open(summary_path, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, indent=4, ensure_ascii=False)
                self.logger.info(f"Saved summary to local storage for article {article.uid}")
            except Exception as e:
                self.logger.error(f"Error saving summary to local storage: {e}")
                
            # Save to Supabase
            self.db.add_summary(
                article.uid, 
                summary, 
                figures, 
                thumbnail
            )

            return summary, figures, thumbnail

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            raise