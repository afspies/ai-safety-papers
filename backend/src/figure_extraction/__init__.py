"""
Figure extraction module for handling various figure extraction methods.
"""

from .figure_extractor_manager import FigureExtractorManager
from .ar5iv_figure_extractor import Ar5ivFigureExtractor
from .pdf_figure_extractor import PdfFigureExtractor

__all__ = ['FigureExtractorManager', 'Ar5ivFigureExtractor', 'PdfFigureExtractor'] 