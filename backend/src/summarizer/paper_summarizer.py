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
from src.utils.config_loader import load_config
from src.utils.pdf_utils import split_pdf_at_appendix

dotenv.load_dotenv()

# openrouter/anthropic/claude-3-7-sonnet-latest
# anthropic/claude-3-7-sonnet-latest
class PaperSummarizer:
    def __init__(self, model_endpoint:str = "anthropic/claude-3-7-sonnet-latest",  db: Optional[SupabaseDB] = None):
        self.model_endpoint = model_endpoint
        self.logger = logging.getLogger(__name__)
        self.db = db

    def extract_figures_from_response(self, content: str) -> Tuple[List[str], Optional[str]]:
        """
        Extract figure IDs and thumbnail from the model response content.
        
        Args:
            content: The text response from the model
            
        Returns:
            Tuple containing:
            - List of figure IDs to display
            - Figure ID to use as thumbnail (or None for default)
        """
        figures_match = re.search(r'<FIGURES>(.*?)</FIGURES>', content, re.DOTALL)
        thumbnail_match = re.search(r'<THUMBNAIL>(.*?)</THUMBNAIL>', content, re.DOTALL)
        
        # Debug the regex matches
        self.logger.info(f"Figures match found: {figures_match is not None}")
        self.logger.info(f"Thumbnail match found: {thumbnail_match is not None}")

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
        else:
            # If no explicit <FIGURES> tag, extract figures from the summary content itself
            # Find all <FIGURE_ID> tags in the content
            figure_refs = re.findall(r'<FIGURE_ID>(\d+)(\.([a-z]))?\</FIGURE_ID>', content, re.DOTALL)
            for ref in figure_refs:
                fig_num = ref[0]
                subfig_letter = ref[2]  # Will be None/empty for main figures
                
                if subfig_letter:
                    figures.append(f"{fig_num}.{subfig_letter}")
                elif fig_num not in figures:  # Avoid duplicates
                    figures.append(fig_num)

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
                
        return figures, thumbnail

    def summarize(self, article: Article, ignore_existing_summary: bool = False) -> Tuple[str, List[str], Optional[str]]:
        """
        Summarize the paper and return the summary, list of figures to display, and thumbnail figure.
        Also generates and stores a markdown summary but doesn't return it to maintain compatibility.
        
        Args:
            article: An Article instance with a PDF path set
            
        Returns:
            Tuple containing:
            - Summary text with figure placeholders
            - List of figure IDs to display
            - Figure ID to use as thumbnail (or None for default)
            
        Raises:
            ValueError: If PDF is not available or model call fails
        """
        # Check for existing summary in Supabase first
        if self.db is None:
            self.db = SupabaseDB()
        
        # First, try to get the appendix_page_number from Supabase if not already set
        if article.appendix_page_number is None:
            try:
                # Query paper details to get the appendix_page_number
                paper_details = self.db.client.table('papers').select('appendix_page_number').eq('id', article.uid).execute()
                if paper_details.data and paper_details.data[0].get('appendix_page_number') is not None:
                    article.appendix_page_number = paper_details.data[0]['appendix_page_number']
                    self.logger.info(f"Loaded appendix page number {article.appendix_page_number} from Supabase for article {article.uid}")
            except Exception as e:
                self.logger.warning(f"Error loading appendix page number from Supabase: {e}")
        
        if not ignore_existing_summary:
            summary_data = self.db.get_summary(article.uid)
            if summary_data:
                self.logger.info(f"Found existing summary in Supabase for article {article.uid}")
                
                # Check if we need to extract figures
                if not summary_data['display_figures']:
                    self.logger.info("Existing summary has empty display_figures. Attempting to extract figures from summary content.")
                    summary_content = summary_data['summary']
                    
                    # Find all <FIGURE_ID> tags in the content
                    figure_refs = re.findall(r'<FIGURE_ID>(\d+)(\.([a-z]))?\</FIGURE_ID>', summary_content)
                    figures = []
                    
                    for ref in figure_refs:
                        fig_num = ref[0]
                        subfig_letter = ref[2]  # Will be None/empty for main figures
                        
                        # Add the figure to our list if not already there
                        if subfig_letter:
                            figures.append(f"{fig_num}.{subfig_letter}")
                        elif fig_num not in figures:  # Avoid duplicates for main figures
                            figures.append(fig_num)
                    
                    if figures:
                        self.logger.info(f"Extracted figure IDs: {figures}")
                        summary_data['display_figures'] = figures
                        
                        # update the db
                        self.db.add_summary(
                            article.uid, 
                            summary_data['summary'],
                            figures,
                            summary_data.get('thumbnail_figure'),
                            summary_data.get('markdown_summary', '')
                        )
                    else:
                        self.logger.info("No figures found in existing summary content.")
                    
                # Generate markdown summary if it doesn't exist
                markdown_summary = summary_data.get('markdown_summary', '')
                if not markdown_summary:
                    self.logger.info("Generating markdown summary from existing summary")
                    markdown_summary = self.post_process_summary_to_markdown(article.uid, summary_data['summary'])
                    
                    # Update the database with the markdown summary
                    self.db.add_summary(
                        article.uid,
                        summary_data['summary'],
                        summary_data['display_figures'],
                        summary_data.get('thumbnail_figure'),
                        markdown_summary
                    )
                    
                # Return only the original 3 values for backward compatibility
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
                        
                    # Check if we need to extract figures
                    if not summary_data['display_figures']:
                        self.logger.info("Local summary has empty display_figures. Attempting to extract figures.")
                        # Call the model to get the full content for figure extraction
                        if article.pdf_path and article.pdf_path.exists():
                            try:
                                model_response = self._get_model_response(article.pdf_path)
                                figures, thumbnail = self.extract_figures_from_response(model_response)
                                
                                # Update the summary data with extracted figures
                                summary_data['display_figures'] = figures
                                summary_data['thumbnail_figure'] = thumbnail or summary_data.get('thumbnail_figure')
                                
                                # Save updated data
                                with open(summary_path, 'w', encoding='utf-8') as f:
                                    json.dump(summary_data, f, indent=4, ensure_ascii=False)
                                    
                            except Exception as e:
                                self.logger.warning(f"Error extracting figures from local summary: {e}")
                    
                    # Generate markdown summary
                    markdown_summary = self.post_process_summary_to_markdown(article.uid, summary_data['summary'])
                    
                    # Store in Supabase for future use
                    try:
                        self.db.add_summary(
                            article.uid, 
                            summary_data['summary'], 
                            summary_data['display_figures'], 
                            summary_data.get('thumbnail_figure'),
                            markdown_summary
                        )
                        self.logger.info(f"Migrated local summary to Supabase for article {article.uid}")
                    except Exception as e:
                        self.logger.warning(f"Error migrating summary to Supabase: {e}")
                        
                    # Return only the original 3 values for backward compatibility
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

        # Split the PDF if appendix_page_number is provided
        pdf_to_summarize = article.pdf_path
        if hasattr(article, 'appendix_page_number') and article.appendix_page_number:
            self.logger.info(f"Splitting PDF at appendix page {article.appendix_page_number}")
            body_pdf, appendix_pdf = split_pdf_at_appendix(
                article.pdf_path, 
                article.appendix_page_number
            )
            
            if body_pdf and body_pdf.exists():
                self.logger.info(f"Using body-only PDF for summarization: {body_pdf}")
                pdf_to_summarize = body_pdf
                # Store paths in the article object for future reference
                article.body_pdf_path = body_pdf
                article.appendix_pdf_path = appendix_pdf
        
        # Call the model using the appropriate PDF and handle errors properly
        try:
            model_response = self._get_model_response(pdf_to_summarize)
            
            if not model_response:
                self.logger.error(f"Empty response from model for article {article.uid}")
                raise ValueError("Failed to generate summary: empty model response")
        except Exception as e:
            self.logger.error(f"Error during model call for article {article.uid}: {e}")
            raise ValueError(f"Failed to generate summary: {str(e)}")
        
        # Parse the response using the XML tag structure - use more greedy matching
        summary_match = re.search(r'<SUMMARY>(.*?)</SUMMARY>', model_response, re.DOTALL)
        
        # If the normal match doesn't work, try a more expansive pattern
        if not summary_match:
            # Try matching everything after # Paper Summary
            summary_match = re.search(r'# Paper Summary(.*?)$', model_response, re.DOTALL)
            
        # Debug - log the first few characters of the matched summary
        if summary_match:
            self.logger.info(f"Summary match first 100 chars: {summary_match.group(1)[:100]}")
            self.logger.info(f"Summary match length: {len(summary_match.group(1))}")
        else:
            self.logger.error(f"Failed to extract summary from model response for article {article.uid}")
            raise ValueError("Failed to generate summary: could not extract summary from model response")
        
        # Debug the regex match
        self.logger.info(f"Summary match found: {summary_match is not None}")

        summary = summary_match.group(1).strip() if summary_match else ""
        
        if not summary:
            self.logger.error(f"Empty summary extracted from model response for article {article.uid}")
            raise ValueError("Failed to generate summary: empty summary extracted from model response")
        
        # Extract figures and thumbnail
        figures, thumbnail = self.extract_figures_from_response(model_response)
        
        # Generate markdown summary
        markdown_summary = self.post_process_summary_to_markdown(article.uid, summary)

        # Save the summary data
        summary_data = {
            'summary': summary,
            'display_figures': figures,
            'thumbnail_figure': thumbnail,
            'markdown_summary': markdown_summary
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
            thumbnail,
            markdown_summary
        )

        # Return only the original 3 values for backward compatibility
        return summary, figures, thumbnail

    def _get_model_response(self, pdf_path: Path) -> str:
        """
        Get the response from the model for the given PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            The text response from the model
        """
        # Read PDF file as base64
        with open(pdf_path, 'rb') as f:
            pdf_data = base64.b64encode(f.read()).decode('utf-8')

        try:
            # Call LiteLLM completion
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

            # Extract content from the response
            content = response.choices[0].message.content
            
            # Log the full response for debugging
            self.logger.info(f"Full response from LiteLLM: {content}")
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error calling model: {e}")
            raise

    def post_process_summary_to_markdown(self, article_id: str, summary: str) -> str:
        """
        Post-process the summary text to convert figure ID tags to markdown image links.
        
        Args:
            article_id: The article ID
            summary: The raw summary with <FIGURE_ID> tags
            
        Returns:
            The processed markdown summary with proper image links
        """
        if not summary:
            return ""
        
        self.logger.info(f"Post-processing summary to markdown for article {article_id}")
        
        # First get all figures for this paper to precompute subfigure relationships
        all_figures = {}
        figure_has_subfigures = {}
        subfigure_map = {}
        
        if self.db:
            # First, scan the local folders for figures
            config = load_config()
            data_dir = Path(config.get('data_dir', 'data'))
            figures_dir = data_dir / article_id / "figures"
            
            self.logger.info(f"Checking local figures directory: {figures_dir}")
            
            if figures_dir.exists():
                # Check for figures and subfigures
                for fig_path in figures_dir.glob("*.png"):
                    fig_id = fig_path.stem
                    self.logger.info(f"Found local figure: {fig_id}")
                    
                    # Check if it's a subfigure
                    subfig_match = re.match(r'(fig\d+)_([a-z])', fig_id)
                    if subfig_match:
                        main_id = subfig_match.group(1)
                        subfig_letter = subfig_match.group(2)
                        
                        # Mark the main figure as having subfigures
                        figure_has_subfigures[main_id] = True
                        
                        # Add to subfigure map using letter as key to avoid duplicates
                        if main_id not in subfigure_map:
                            subfigure_map[main_id] = {}
                        # Only add if not already in map
                        if subfig_letter not in subfigure_map[main_id]:
                            subfigure_map[main_id][subfig_letter] = {'figure_id': fig_id, 'local_path': str(fig_path)}
                        
                        self.logger.info(f"Identified as subfigure of {main_id}")
            
            # Now check Supabase for figure data
            paper_figures = self.db.get_paper_figures(article_id)
            self.logger.info(f"Found {len(paper_figures)} figures in Supabase")
            
            for fig in paper_figures:
                fig_id = fig.get('figure_id', '')
                all_figures[fig_id] = fig
                self.logger.info(f"Found figure in Supabase: {fig_id}")
                
                # Check if it's a subfigure
                subfig_match = re.match(r'(fig\d+)_([a-z])', fig_id)
                if subfig_match:
                    main_id = subfig_match.group(1)
                    subfig_letter = subfig_match.group(2)
                    
                    # Mark the main figure as having subfigures
                    figure_has_subfigures[main_id] = True
                    
                    # Add to subfigure map using letter as key to avoid duplicates
                    if main_id not in subfigure_map:
                        subfigure_map[main_id] = {}
                    # Only add if not already in map
                    if subfig_letter not in subfigure_map[main_id]:
                        subfigure_map[main_id][subfig_letter] = fig
                    
                    self.logger.info(f"Identified as subfigure of {main_id}")
        
        # Log what we found
        for main_id, has_subfigs in figure_has_subfigures.items():
            if has_subfigs:
                subfigs = subfigure_map.get(main_id, {})
                self.logger.info(f"Figure {main_id} has {len(subfigs)} subfigures: {list(subfigs.keys())}")
        
        # Regular expression to find figure ID tags
        figure_pattern = r'<FIGURE_ID>(\d+)(\.([a-z]))?\</FIGURE_ID>'
        
        def replace_figure(match):
            fig_num = match.group(1)
            subfig_letter = match.group(3)  # Will be None for main figures
            
            # Ensure proper formatting of figure IDs
            fig_id_raw = f"{fig_num}"
            if subfig_letter:
                fig_id_raw += f".{subfig_letter}"
            
            self.logger.info(f"Processing figure reference: {fig_id_raw}")
            
            if subfig_letter:
                # This is a specific subfigure reference
                fig_id = f"fig{fig_num}_{subfig_letter}"
                display_text = f"Figure {fig_num}.{subfig_letter}"
                
                self.logger.info(f"Looking for subfigure: {fig_id}")
                
                # Get the figure URL from Supabase
                if self.db:
                    figure_url = self.db.get_figure_url(article_id, fig_id)
                    if figure_url:
                        self.logger.info(f"Found URL for subfigure {fig_id}: {figure_url}")
                        # Return a markdown image link for this specific subfigure
                        return f"\n\n![{display_text}]({figure_url})\n\n"
                    else:
                        self.logger.warning(f"No URL found for subfigure {fig_id}")
                
                # If we couldn't get a URL, just return the figure reference as text
                return display_text
            else:
                # This is a reference to a main figure, which might have subfigures
                main_fig_id = f"fig{fig_num}"
                display_text = f"Figure {fig_num}"
                
                self.logger.info(f"Looking for main figure: {main_fig_id}")
                
                # Check if this figure has subfigures using our precomputed map
                has_subfigs = figure_has_subfigures.get(main_fig_id, False)
                if has_subfigs and main_fig_id in subfigure_map:
                    self.logger.info(f"Figure {main_fig_id} has subfigures, processing them")
                    # Sort subfigures by letter
                    subfigures = sorted(subfigure_map[main_fig_id].items())
                    
                    # Create a markdown grid with all subfigures
                    subfigure_md = []
                    for letter, subfig in subfigures:
                        subfig_id = f"{main_fig_id}_{letter}"
                        subfig_url = self.db.get_figure_url(article_id, subfig_id)
                        if subfig_url:
                            self.logger.info(f"Found URL for subfigure {subfig_id}: {subfig_url}")
                            subfigure_md.append(f"![Figure {fig_num}.{letter}]({subfig_url})")
                        else:
                            self.logger.warning(f"No URL found for subfigure {subfig_id}")
                    
                    # Return a formatted figure group
                    if subfigure_md:
                        return f"\n\n**{display_text}**\n\n" + "\n\n".join(subfigure_md) + "\n\n"
                    else:
                        self.logger.warning(f"No subfigure URLs found for {main_fig_id}")
                
                # Regular figure or couldn't get subfigures
                if self.db:
                    figure_url = self.db.get_figure_url(article_id, main_fig_id)
                    if figure_url:
                        self.logger.info(f"Found URL for main figure {main_fig_id}: {figure_url}")
                        # Return a markdown image link
                        return f"\n\n![{display_text}]({figure_url})\n\n"
                    else:
                        self.logger.warning(f"No URL found for main figure {main_fig_id}")
                
                # If we couldn't get a URL, just return the figure reference as text
                return display_text
        
        # Replace all figure tags with markdown
        markdown_summary = re.sub(figure_pattern, replace_figure, summary)
        
        return markdown_summary

    def get_markdown_summary(self, article_id: str) -> str:
        """
        Get the markdown-formatted summary for an article.
        
        Args:
            article_id: The article ID
            
        Returns:
            The markdown-formatted summary
        """
        if self.db is None:
            self.db = SupabaseDB()
        
        summary_data = self.db.get_summary(article_id)
        if summary_data:
            markdown_summary = summary_data.get('markdown_summary', '')
            if markdown_summary:
                return markdown_summary
            
            # If no markdown summary exists, generate one from the raw summary
            if summary_data.get('summary'):
                markdown_summary = self.post_process_summary_to_markdown(article_id, summary_data['summary'])
                
                # Save the generated markdown
                self.db.add_summary(
                    article_id,
                    summary_data['summary'],
                    summary_data['display_figures'],
                    summary_data.get('thumbnail_figure'),
                    markdown_summary
                )
                
                return markdown_summary
            
        return ""