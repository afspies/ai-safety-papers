#!/usr/bin/env python3
"""
Simple test script to verify the figure extraction functionality.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.src.figure_extraction import FigureExtractorManager, Ar5ivFigureExtractor, PdfFigureExtractor

def main():
    # Initialize the figure extractor manager
    manager = FigureExtractorManager()
    
    # Print info about available extractors
    print(f"FigureExtractorManager initialized with {len(manager.extractors)} extractors:")
    for i, extractor in enumerate(manager.extractors):
        print(f"  {i+1}. {extractor.__class__.__name__}")
    
    # Initialize individual extractors
    ar5iv_extractor = Ar5ivFigureExtractor()
    pdf_extractor = PdfFigureExtractor()
    
    print("\nSuccessfully imported and initialized all figure extractors.")

if __name__ == "__main__":
    main() 