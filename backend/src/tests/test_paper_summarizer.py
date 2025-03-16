import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import os
import yaml
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.summarizer.paper_summarizer import PaperSummarizer
from src.models.article import Article

class TestPaperSummarizer(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        # Load API key from config
        with open(Path(project_root).parent / "secrets" / "config.yaml", "r") as f:
            config = yaml.safe_load(f)
        self.api_key = config["anthropic"]["api_key"]
        self.summarizer = PaperSummarizer(self.api_key)
        
        # Create mock article
        self.article = Mock(spec=Article)
        self.article.data_folder = Path(__file__).parent / "test_data"
        self.article.pdf_path = self.article.data_folder / "paper.pdf"
        
        # Ensure test directory exists
        self.article.data_folder.mkdir(exist_ok=True)
        
        # Sample parsed document with figures
        self.sample_doc = {
            "pages": [
                {
                    "figures": [
                        {"boxes": [{"text": "Figure 1"}]}
                    ],
                    "captions": [
                        {"text": "Architecture diagram", "boxes": [{}]}
                    ]
                },
                {
                    "figures": [
                        {"boxes": [{"text": "Figure 2"}]}
                    ],
                    "captions": [
                        {"text": "Results graph", "boxes": [{}]}
                    ]
                }
            ]
        }
        
        # Create parsed_doc.json in test directory
        with open(self.article.data_folder / "parsed_doc.json", 'w') as f:
            json.dump(self.sample_doc, f)

    @patch('anthropic.Anthropic')
    @patch('fitz.open')
    def test_summarize(self, mock_fitz_open, mock_anthropic):
        """Test the complete summarization process with mock article."""
        # Mock PDF content
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Abstract\nThis is a test paper about AI safety."
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc

        # Set up mock response from Claude
        mock_response = MagicMock()
        mock_response.content = [{
            "text": """<SUMMARY>
            This paper presents a novel approach to AI safety.
            <FIGURE_ID>0</FIGURE_ID> shows the system architecture.
            The results, demonstrated in <FIGURE_ID>1</FIGURE_ID>, indicate improved safety metrics.
            </SUMMARY>
            <FIGURES>
            0
            1
            </FIGURES>
            <THUMBNAIL>
            0
            </THUMBNAIL>"""
        }]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        # Test summarization
        summary, figures, thumbnail = self.summarizer.summarize(self.article)

        # Verify the summary content
        self.assertIn("novel approach to AI safety", summary)
        self.assertEqual(figures, ["0", "1"])
        self.assertEqual(thumbnail, "0")
        
        # Verify that the API was called with correct content
        mock_anthropic.return_value.messages.create.assert_called_once()
        call_args = mock_anthropic.return_value.messages.create.call_args[1]
        self.assertIn("messages", call_args)
        self.assertIn("Abstract", call_args["messages"][0]["content"])

    @patch('anthropic.Anthropic')
    @patch('fitz.open')
    def test_summarize_no_suitable_thumbnail(self, mock_fitz_open, mock_anthropic):
        """Test summarization when no figure is suitable for thumbnail."""
        # Mock PDF content
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Abstract\nThis is a test paper about AI safety."
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc

        mock_response = MagicMock()
        mock_response.content = [{
            "text": """<SUMMARY>
            This paper presents a novel approach to AI safety.
            </SUMMARY>
            <FIGURES>
            </FIGURES>
            <THUMBNAIL>
            NONE
            </THUMBNAIL>"""
        }]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        summary, figures, thumbnail = self.summarizer.summarize(self.article)

        self.assertIsNone(thumbnail)
        self.assertEqual(figures, [])

if __name__ == '__main__':
    unittest.main()