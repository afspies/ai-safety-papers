import anthropic
from typing import Tuple, List, Optional, Dict, Any
import json
from pathlib import Path
import logging
import base64
import re
from src.models.article import Article
from src.models.supabase import SupabaseDB

class PaperSummarizer:
    def __init__(self, api_key: str, development_mode: bool = False):
        if not development_mode:
            self.client = anthropic.Anthropic(api_key=api_key)
        self.development_mode = development_mode
        self.logger = logging.getLogger(__name__)

    def summarize(self, article: Article) -> Tuple[str, List[str], Optional[str]]:
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
        try:
            db = SupabaseDB()
            summary_data = db.get_summary(article.uid)
            if summary_data:
                self.logger.info(f"Found existing summary in Supabase for article {article.uid}")
                return (
                    summary_data['summary'],
                    summary_data['display_figures'],
                    summary_data.get('thumbnail_figure')
                )
        except Exception as e:
            self.logger.warning(f"Error checking Supabase for summary: {e}. Continuing with local check.")
            
        # Check for existing summary in local storage
        summary_path = article.data_folder / "summary.json"
        if summary_path.exists():
            self.logger.info(f"Found existing summary in local storage for article {article.uid}")
            try:
                with open(summary_path, 'r', encoding='utf-8') as f:
                    summary_data = json.load(f)
                    
                # Store in Supabase for future use
                try:
                    db = SupabaseDB()
                    db.add_summary(
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

        # In development mode, generate mock summary
        if self.development_mode:
            self.logger.info(f"Development mode: Generating mock summary for article {article.uid}")
            return self._generate_mock_summary(article)

        # Production mode - continue with actual API call
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

            # Save to local storage as backup
            try:
                with open(summary_path, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, indent=4, ensure_ascii=False)
                self.logger.info(f"Saved summary to local storage for article {article.uid}")
            except Exception as e:
                self.logger.error(f"Error saving summary to local storage: {e}")
                
            # Save to Supabase
            try:
                db = SupabaseDB()
                db.add_summary(
                    article.uid, 
                    summary, 
                    figures, 
                    thumbnail
                )
                self.logger.info(f"Saved summary to Supabase for article {article.uid}")
            except Exception as e:
                self.logger.error(f"Error saving summary to Supabase: {e}")
                # Continue anyway - local storage was used as backup

            return summary, figures, thumbnail

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            raise
            
    def _generate_mock_summary(self, article: Article) -> Tuple[str, List[str], str]:
        """Generate a mock summary for development mode."""
        import hashlib
        import random
        
        # Create deterministic random seed based on article ID
        seed = int(hashlib.md5(article.uid.encode()).hexdigest(), 16) % (10**8)
        random.seed(seed)
        
        # Create a list of figure numbers (1-4)
        figures = [str(i) for i in range(1, random.randint(3, 5))]
        
        # Select a thumbnail figure (usually the first one)
        thumbnail = figures[0] if figures else "1"
        
        # Create a data directory if it doesn't exist
        article.data_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate a mock detailed summary
        summary = f"""# Paper Summary

This paper presents a novel approach to AI safety in large language models. The authors use a multi-agent framework to address the challenge of ensuring robust alignment in generative AI systems. Their work makes several important contributions:

## Key Contributions
- Development of a new evaluation framework for measuring safety across diverse scenarios
- Introduction of a hierarchical oversight mechanism that improves alignment without sacrificing performance
- Empirical demonstration that their approach reduces harmful outputs by 78% compared to baseline models
- Release of a comprehensive benchmark dataset for evaluating safety measures in language models

## Problem Statement and Background
Current approaches to AI safety often trade off performance for safety, resulting in models that are either unsafe or significantly less capable. <FIGURE_ID>{figures[0]}</FIGURE_ID> illustrates this trade-off, showing how existing methods create a Pareto frontier where improvements in safety correspond to decreases in model capabilities. The authors argue that this trade-off is not fundamental but rather a limitation of current methodologies that focus primarily on output filtering and fine-tuning with human feedback.

Traditional methods have focused on reinforcement learning from human feedback (RLHF) and rule-based filtering. While these approaches show promise, they struggle with complex scenarios where harmful content might be contextually appropriate (such as in educational contexts) or where harmful requests are subtly disguised.

## Methods
The authors propose a hierarchical oversight framework that combines multiple complementary safety mechanisms. <FIGURE_ID>{figures[1] if len(figures) > 1 else figures[0]}</FIGURE_ID> shows the architecture of this framework, which consists of three main components: a base language model, a set of specialized safety evaluators, and a meta-controller that mediates between them. The specialized evaluators focus on different aspects of safety, including factuality, bias, toxicity, and potential for misuse.

The meta-controller is trained to recognize when to defer to specific evaluators based on context and request type. This allows the system to apply appropriate safety measures without unnecessarily restricting the model in contexts where certain types of content are appropriate. The authors utilize a multi-agent training procedure where the safety evaluators and meta-controller are iteratively improved through adversarial examples and feedback.

{f"<FIGURE_ID>{figures[2]}</FIGURE_ID> demonstrates their training methodology, showing how the system improves over time through exposure to increasingly sophisticated adversarial prompts. The training curves indicate that the most significant improvements occur in the first 1000 iterations, with diminishing returns thereafter." if len(figures) > 2 else ""}

## Results
The authors evaluated their approach on a comprehensive benchmark that included both standard safety datasets and novel adversarial examples designed to circumvent typical safety measures. {f"<FIGURE_ID>{figures[3]}</FIGURE_ID>" if len(figures) > 3 else f"<FIGURE_ID>{figures[-1]}</FIGURE_ID>"} presents the main results, showing that their hierarchical approach reduced harmful outputs by 78% compared to baseline models, while maintaining 96% of performance on standard capability benchmarks.

Notably, the system showed particular strength in handling contextually complex scenarios where rule-based approaches typically fail. For example, it could appropriately discuss harmful topics in educational contexts while refusing similar requests when the intent appeared harmful. Ablation studies confirmed that the meta-controller was critical to this performance, as removing it resulted in a 45% increase in false positive safety interventions.

## Implications and Limitations
This work demonstrates that the trade-off between safety and capability can be significantly mitigated through more nuanced, context-aware approaches to AI safety. The hierarchical framework provides a promising direction for future research, particularly as models continue to increase in capability and potential for misuse.

However, the authors acknowledge several limitations. Their approach requires significant computational resources for training the multiple components. Additionally, while their method shows robust performance against current adversarial techniques, they emphasize that safety is an ongoing challenge requiring continuous updates as new evasion strategies emerge. Finally, they note that their evaluation, while comprehensive, still cannot capture the full range of potential real-world harmful uses.

## Related Work and Future Directions
This research builds upon previous work in RLHF, constitutional AI, and multi-agent systems, but distinguishes itself through the hierarchical integration of specialized safety evaluators. Future work could extend this approach by incorporating more diverse evaluators, improving the meta-controller's ability to explain its decisions, and developing more efficient training methods to reduce computational requirements. The authors also suggest that similar hierarchical approaches could be beneficial for other AI alignment challenges beyond safety, such as truthfulness and helpfulness.
"""
        
        # Create the summary data directory if needed
        summary_path = article.data_folder / "summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the mock summary
        summary_data = {
            'summary': summary,
            'display_figures': figures,
            'thumbnail_figure': thumbnail
        }
        
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved mock summary for article {article.uid}")
        except Exception as e:
            self.logger.error(f"Error saving mock summary: {e}")
        
        return summary, figures, thumbnail
