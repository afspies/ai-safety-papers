from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

class Article:
    """Class representing a scientific article."""
    
    def __init__(
        self,
        uid: str,
        title: str,
        url: str,
        authors: List[str] = None,
        abstract: str = "",
        pdf_path: Optional[Path] = None,
        data_folder: Optional[Path] = None,
        website_content_path: Optional[Path] = None,
        venue: str = "",
        submitted_date: Optional[datetime] = None
    ):
        self.uid = uid
        self.title = title
        self.url = url
        self.authors = authors or []
        self.abstract = abstract
        self.pdf_path = pdf_path
        self.data_folder = data_folder
        self.website_content_path = website_content_path
        self.venue = venue
        self.submitted_date = submitted_date
        self.tldr = ""  # Optional TL;DR summary
        self.tags: List[str] = []  # Optional tags/keywords