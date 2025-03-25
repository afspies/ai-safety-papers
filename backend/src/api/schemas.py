from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class PaperSummary(BaseModel):
    """Schema for paper summary in list view."""
    uid: str
    title: str
    authors: List[str]
    abstract: str
    tldr: str
    thumbnail_url: str
    submitted_date: Optional[datetime] = None
    highlight: bool = False
    tags: List[str] = Field(default_factory=list)


class FigureSchema(BaseModel):
    """Schema for figure data."""
    id: str
    caption: str
    url: str
    has_subfigures: bool = False
    subfigures: List[Dict[str, Any]] = Field(default_factory=list)
    type: str = "figure"


class PaperDetail(BaseModel):
    """Schema for detailed paper view."""
    uid: str
    title: str
    authors: List[str]
    abstract: str = ""
    tldr: str = ""
    summary: str = ""  # This will now contain the markdown summary
    raw_summary: str = ""  # Optional field for the raw summary with figure tags
    markdown_summary: str = ""  # Kept for backward compatibility
    url: str = ""
    venue: str = ""
    submitted_date: Optional[datetime] = None
    highlight: bool = False
    tags: List[str] = []
    figures: List[FigureSchema] = []