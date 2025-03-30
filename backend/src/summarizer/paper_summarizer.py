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
                    
                    # Extract figures from the summary using figure ID tags
                    figures = self._extract_figures_from_summary(summary_content)
                    
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
                        summary_content = summary_data['summary']
                        figures = self._extract_figures_from_summary(summary_content)
                        
                        if figures:
                            # Update the summary data with extracted figures
                            summary_data['display_figures'] = figures
                            
                            # Save updated data
                            with open(summary_path, 'w', encoding='utf-8') as f:
                                json.dump(summary_data, f, indent=4, ensure_ascii=False)
                    
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
        
        # Extract figures from the summary
        figures = self._extract_figures_from_summary(summary)
        
        # For backward compatibility, still try to extract thumbnail from response
        thumbnail_match = re.search(r'<THUMBNAIL>(.*?)</THUMBNAIL>', model_response, re.DOTALL)
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
            summary_path = article.data_folder / "summary.json"
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
                            { # PDF file
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data
                                },
                                "citations": {"enabled": True},
                                "context": "The PDF of the paper you should summarize."
                            },
                            { # Prompt
                                "type": "text",
                                "text": summarization_prompt,
                                # "cache_control": {"type": "ephemeral"},
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
        
        # Get all figure URLs for this article
        figure_urls = self._get_figure_urls(article_id)
        
        # Process the markdown with the figure URLs
        return self._process_markdown_with_figures(summary, figure_urls, article_id)
    
    def _get_figure_urls(self, article_id: str) -> dict:
        """
        Get all figure URLs for an article.
        
        Args:
            article_id: The article ID
            
        Returns:
            Dictionary mapping figure IDs to their URLs
        """
        figure_urls = {}
        
        if not self.db:
            self.db = SupabaseDB()
            
        # Get figures from Supabase
        paper_figures = self.db.get_paper_figures(article_id)
        
        # Track subfigures by main figure number
        subfigures_by_main = {}
        
        for fig in paper_figures:
            fig_id = fig.get('figure_id', '')
            if fig_id:
                url = self.db.get_figure_url(article_id, fig_id)
                if url:
                    # Store original figure ID mapping
                    figure_urls[fig_id] = url
                    
                    # Check if this is a subfigure (fig7_a format)
                    subfig_match = re.match(r'fig(\d+)[_.]([a-zA-Z])', fig_id)
                    if subfig_match:
                        main_num = subfig_match.group(1)
                        subfig_letter = subfig_match.group(2).lower()  # Normalize to lowercase
                        
                        # Store standardized format (7.a)
                        normalized_key = f"{main_num}.{subfig_letter}"
                        figure_urls[normalized_key] = url
                        
                        # Track this subfigure under its main figure number
                        if main_num not in subfigures_by_main:
                            subfigures_by_main[main_num] = []
                        subfigures_by_main[main_num].append((normalized_key, url))
                    else:
                        # For main figures (fig7 format), also store as just the number
                        num_match = re.match(r'fig(\d+)', fig_id)
                        if num_match:
                            main_num = num_match.group(1)
                            figure_urls[main_num] = url
        
        self.logger.info(f"Found {len(figure_urls)} figure URLs for article {article_id}")
        return figure_urls
    
    def _process_markdown_with_figures(self, summary: str, figure_urls: dict, article_id: str) -> str:
        """
        Process markdown by replacing figure tags and adding figure images.
        
        Args:
            summary: The raw summary with <FIGURE_ID> tags
            figure_urls: Dictionary mapping figure IDs to their URLs
            article_id: The article ID for logging purposes
            
        Returns:
            The processed markdown with figure images
        """
        self.logger.info(f"Processing markdown with figures for article {article_id}")
        
        # Regular expression to find figure ID tags - handle both upper and lowercase subfigure letters
        figure_pattern = r'<FIGURE_ID>(\d+)(\.([a-zA-Z]))?\</FIGURE_ID>'
        
        # Identify figures that only have subfigures but no main figure
        main_figs_with_only_subfigs = set()
        for key in figure_urls.keys():
            subfig_match = re.match(r'fig(\d+)[_.]([a-zA-Z])', key)
            if subfig_match:
                main_num = subfig_match.group(1)
                # Check if this main figure exists directly
                if f"fig{main_num}" not in figure_urls:
                    main_figs_with_only_subfigs.add(main_num)
        
        # Split into lines for line-by-line processing
        lines = summary.split('\n')
        result_lines = []
        
        # Track which figures we've already inserted
        processed_figures = set()
        # Track the URLs we've already inserted to avoid duplicates
        processed_urls = set()
        
        # Process each line
        for line in lines:
            # Find all figure references in this line
            matches = list(re.finditer(figure_pattern, line))
            
            # Replace figure tags with bold text
            processed_line = line
            line_figures = []  # Figures to add after this line
            
            for match in matches:
                fig_num = match.group(1)
                subfig_letter = match.group(3)  # Will be None for main figures
                
                # Check if this is a main figure that only has subfigures
                if not subfig_letter and fig_num in main_figs_with_only_subfigs:
                    # This is a main figure with only subfigures - don't insert it directly,
                    # but we'll still replace the tag with bold text
                    display_text = f"Figure {fig_num}"
                    processed_line = processed_line.replace(match.group(0), f"**{display_text}**")
                    
                    # Instead of showing the main figure, find and show all its subfigures
                    subfigure_keys = []
                    
                    # Check standard subfigure pattern (e.g., "7.a", "7.b")
                    for letter in 'abcdefghijklmnopqrstuvwxyz':
                        subfig_key = f"{fig_num}.{letter}"
                        if subfig_key in figure_urls:
                            subfigure_keys.append((subfig_key, f"Figure {fig_num}.{letter}"))
                    
                    # Also check for alternative subfigure formats in the original figure_urls keys
                    for key in figure_urls.keys():
                        # Check for fig7_a format
                        if key.startswith(f"fig{fig_num}_") or key.startswith(f"fig{fig_num}."):
                            subfig_letter = key[-1].lower()
                            subfig_key = f"{fig_num}.{subfig_letter}"
                            display = f"Figure {fig_num}.{subfig_letter}"
                            
                            # Only add if not already found
                            if (subfig_key, display) not in subfigure_keys:
                                subfigure_keys.append((subfig_key, display))
                    
                    # Add each subfigure if found
                    for subfig_key, display_text in subfigure_keys:
                        if subfig_key not in processed_figures:
                            figure_url = figure_urls.get(subfig_key)
                            if figure_url and figure_url not in processed_urls:
                                figure_md = f"![{display_text}]({figure_url})"
                                line_figures.append(figure_md)
                                processed_figures.add(subfig_key)
                                processed_urls.add(figure_url)
                                self.logger.info(f"Added subfigure markdown for {subfig_key} (display: {display_text})")
                            elif figure_url:
                                # Mark as processed even if we skip showing the URL
                                processed_figures.add(subfig_key)
                                self.logger.info(f"Skipping duplicate URL for subfigure {subfig_key} (URL already shown)")
                    
                    # Skip the rest of the processing for this figure since we've handled it specially
                    continue
                
                # Regular processing for other figures
                # Create figure display text - preserve original case for display
                display_text = f"Figure {fig_num}"
                if subfig_letter:
                    display_text = f"Figure {fig_num}.{subfig_letter}"
                
                # Replace the tag with bold text
                processed_line = processed_line.replace(match.group(0), f"**{display_text}**")
                
                # Generate figure keys for lookup - normalize to lowercase for consistency
                fig_key = fig_num
                if subfig_letter:
                    fig_key = f"{fig_num}.{subfig_letter.lower()}"
                
                # Try to find the figure URL
                figure_url = figure_urls.get(fig_key)
                
                # If we found a URL and haven't processed this figure yet, add it
                if figure_url and fig_key not in processed_figures:
                    # Check for duplicate URLs to avoid showing the same image twice
                    if figure_url not in processed_urls:
                        figure_md = f"![{display_text}]({figure_url})"
                        line_figures.append(figure_md)
                        processed_urls.add(figure_url)
                    else:
                        self.logger.info(f"Skipping duplicate URL for {fig_key} (URL already shown)")
                    
                    # Mark as processed even if we skipped the URL
                    processed_figures.add(fig_key)
                    self.logger.info(f"Added figure markdown for {fig_key} (display: {display_text})")
                
                # Handle main figure references - always check for subfigures when it's a main figure
                if not subfig_letter:  # This is a main figure reference
                    # Check for subfigures like "7.a", "7.b" or fig7_a, fig7_b
                    subfigure_keys = []
                    
                    # Check standard subfigure pattern (e.g., "7.a", "7.b")
                    for letter in 'abcdefghijklmnopqrstuvwxyz':
                        subfig_key = f"{fig_num}.{letter}"
                        if subfig_key in figure_urls:
                            subfigure_keys.append((subfig_key, f"Figure {fig_num}.{letter}"))
                    
                    # Also check for alternative subfigure formats in the original figure_urls keys
                    for key in figure_urls.keys():
                        # Check for fig7_a format
                        if key.startswith(f"fig{fig_num}_") or key.startswith(f"fig{fig_num}."):
                            subfig_letter = key[-1].lower()
                            subfig_key = f"{fig_num}.{subfig_letter}"
                            display = f"Figure {fig_num}.{subfig_letter}"
                            
                            # Only add if not already found
                            if (subfig_key, display) not in subfigure_keys:
                                subfigure_keys.append((subfig_key, display))
                    
                    # Add each subfigure if found
                    for subfig_key, display_text in subfigure_keys:
                        if subfig_key not in processed_figures:
                            figure_url = figure_urls.get(subfig_key)
                            if figure_url and figure_url not in processed_urls:
                                figure_md = f"![{display_text}]({figure_url})"
                                line_figures.append(figure_md)
                                processed_figures.add(subfig_key)
                                processed_urls.add(figure_url)
                                self.logger.info(f"Added subfigure markdown for {subfig_key} (display: {display_text})")
                            elif figure_url:
                                # Mark as processed even if we skip showing the URL
                                processed_figures.add(subfig_key)
                                self.logger.info(f"Skipping duplicate URL for subfigure {subfig_key} (URL already shown)")
            
            # Add the processed line
            result_lines.append(processed_line)
            
            # Add any figures that were referenced in this line
            if line_figures:
                for figure_md in line_figures:
                    result_lines.append("")  # Empty line before figure
                    result_lines.append(figure_md)
                    result_lines.append("")  # Empty line after figure
        
        # Join all lines into the final markdown
        return "\n".join(result_lines)

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

    def _extract_figures_from_summary(self, summary: str) -> List[str]:
        """
        Extract figure IDs from the summary text.
        
        Args:
            summary: The raw summary text
            
        Returns:
            List of figure IDs extracted from the summary
        """
        figures = []
        
        # Find all <FIGURE_ID> tags in the summary
        figure_refs = re.findall(r'<FIGURE_ID>(\d+)(\.([a-zA-Z]))?\</FIGURE_ID>', summary)
        for ref in figure_refs:
            fig_num = ref[0]
            subfig_letter = ref[2]  # Will be None/empty for main figures
            
            # Add the figure to our list if not already there
            if subfig_letter:
                # Convert subfigure letter to lowercase
                figure_id = f"{fig_num}.{subfig_letter.lower()}"
                if figure_id not in figures:
                    figures.append(figure_id)
            elif fig_num not in figures:  # Avoid duplicates for main figures
                figures.append(fig_num)
        
        self.logger.info(f"Extracted {len(figures)} figure IDs from summary: {figures}")
        return figures

    def regenerate_markdown_summary(self, article_id: str) -> str:
        """
        Regenerate the markdown summary for an article from its raw summary.
        This is useful for fixing markdown rendering issues without regenerating the whole summary.
        
        Args:
            article_id: The article ID
            
        Returns:
            The regenerated markdown summary
        """
        if self.db is None:
            self.db = SupabaseDB()
            
        # Get the existing summary data
        summary_data = self.db.get_summary(article_id)
        if not summary_data or not summary_data.get('summary'):
            self.logger.error(f"No summary found for article {article_id}")
            return ""
            
        # Get the raw summary
        raw_summary = summary_data['summary']
        
        # Regenerate the markdown
        markdown_summary = self.post_process_summary_to_markdown(article_id, raw_summary)
        
        # Update the stored markdown summary
        self.db.add_summary(
            article_id,
            raw_summary,
            summary_data['display_figures'],
            summary_data.get('thumbnail_figure'),
            markdown_summary
        )
        
        self.logger.info(f"Successfully regenerated markdown summary for article {article_id}")
        return markdown_summary