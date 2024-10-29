import json
import requests
import numpy as np
from pathlib import Path
import pymupdf  # Changed from fitz to pymupdf
from papermage.recipes import CoreRecipe
from papermage.visualizers import plot_entities_on_page
from papermage.rasterizers import PDF2ImageRasterizer
from papermage import Document, Entity
from typing import Dict, List, Optional, Union
# from ..summarizer.paper_summarizer import PaperSummarizer

class Article:
    def __init__(self, uid: str, title: str, url_or_path: Union[str, Path]):
        self.uid = uid
        self.title = title
        self.url = url_or_path if isinstance(url_or_path, str) and url_or_path.startswith('http') else None
        self.data_folder = Path(f"./data/{self.uid}")
        self.figures_folder = self.data_folder / "figures"
        self.data_folder.mkdir(parents=True, exist_ok=True)
        self.figures_folder.mkdir(parents=True, exist_ok=True)
        self.pdf_path = Path(url_or_path) if not self.url else self.data_folder / "paper.pdf"
        self.figures: Dict[str, Path] = {}
        self.displayed_figures: List[str] = []
        self.thumbnail_source: Optional[str] = None
        self.parsed_doc: Optional[Document] = None
        self.raw_text: Optional[str] = None
        
        # Initialize by loading or downloading PDF and parsing
        if self.url and not self.pdf_path.exists():
            self.download_pdf()
        print(f"Downloaded PDF to {self.pdf_path}")
        self._ensure_parsed()

    def _ensure_parsed(self) -> Document:
        """Ensure document is parsed, loading from cache if available."""
        if self.parsed_doc is not None and self.raw_text is not None:
            return self.parsed_doc
            
        # Parse raw text using PyMuPDF if not already done
        if self.raw_text is None:
            self._parse_raw_text()
            
        # Load or generate papermage parsing
        parsed_doc_path = self.data_folder / "parsed_doc.json"
        if parsed_doc_path.exists():
            with open(parsed_doc_path, "r") as f:
                self.parsed_doc = Document.from_json(json.load(f))
        else:
            recipe = CoreRecipe()
            self.parsed_doc = recipe.run(str(self.pdf_path))
            # Save the parsed doc
            with open(parsed_doc_path, "w") as f:
                json.dump(self.parsed_doc.to_json(), f, indent=4)
                
        return self.parsed_doc

    def _parse_raw_text(self):
        """Parse raw text from PDF using PyMuPDF."""
        raw_text_path = self.data_folder / "raw_text.txt"
        
        if raw_text_path.exists():
            with open(raw_text_path, "r", encoding="utf-8") as f:
                self.raw_text = f.read()
        else:
            doc = pymupdf.open(str(self.pdf_path))  # Changed from fitz to pymupdf
            all_text = []
            for page in doc:
                text = page.get_text()
                all_text.append(text)
            doc.close()
            
            self.raw_text = " ".join(all_text)
            
            # Cache the raw text
            with open(raw_text_path, "w", encoding="utf-8") as f:
                f.write(self.raw_text)

    def get_raw_text(self) -> str:
        """Get the raw text content of the PDF."""
        if self.raw_text is None:
            self._parse_raw_text()
        return self.raw_text

    def download_pdf(self):
        response = requests.get(self.url)
        response.raise_for_status()
        with open(self.pdf_path, 'wb') as f:
            f.write(response.content)

    def extract_figures(self):
        """Extract figures from the PDF and save them to the figures folder."""
        if not (self.data_folder / "parsed_doc.json").exists():
            self._parse_document()

        with open(self.data_folder / "parsed_doc.json", "r") as f:
            doc = Document.from_json(json.load(f))

        rasterizer = PDF2ImageRasterizer()
        rasterized_image = rasterizer.rasterize(str(self.pdf_path), 300)
        im_w, im_h = rasterized_image[0].pilimage.size

        for page_num in range(len(doc.pages)):
            for figure_num in range(len(doc.pages[page_num].figures)):
                figure = doc.pages[page_num].figures[figure_num]
                figure_box = figure.boxes[0]
                
                # Find matching caption
                matching_caption = self._find_matching_caption(doc.pages[page_num], figure_box)
                
                if matching_caption:
                    # Compute combined bbox for figure and caption
                    combined_bbox = self._compute_combined_bbox(figure_box, matching_caption.boxes[0])
                    
                    # Convert to pixel coordinates and adjust for full width
                    crop_bbox = self._convert_to_pixel_coords(combined_bbox, im_w, im_h)
                    
                    # Crop and save the figure
                    figure_id = f"fig_{page_num}_{figure_num}"
                    figure_path = self.figures_folder / f"{figure_id}.png"
                    cropped_image = rasterized_image[page_num].pilimage.crop(crop_bbox)
                    cropped_image.save(figure_path)
                    
                    self.figures[figure_id] = figure_path

        # Save figures metadata
        self._save_figures_metadata()

    def _find_matching_caption(self, page, figure_box):
        """Find the caption that best matches the figure."""
        matching_caption = None
        min_distance = float('inf')
        
        figure_center_x = figure_box.l + figure_box.w/2
        figure_center_y = figure_box.t + figure_box.h/2
        
        for caption in page.captions:
            caption_box = caption.boxes[0]
            caption_center_x = caption_box.l + caption_box.w/2
            caption_center_y = caption_box.t + caption_box.h/2
            
            distance = ((figure_center_x - caption_center_x)**2 + 
                       (figure_center_y - caption_center_y)**2)**0.5
            
            vertical_bias = 2.0 if caption_center_y > figure_center_y else 1.0
            weighted_distance = distance * vertical_bias
            
            if weighted_distance < min_distance:
                min_distance = weighted_distance
                matching_caption = caption
        
        return matching_caption

    def _compute_combined_bbox(self, figure_box, caption_box):
        """Compute bounding box containing both figure and caption."""
        l = min(figure_box.l, caption_box.l)
        t = min(figure_box.t, caption_box.t)
        w = max(figure_box.l + figure_box.w, caption_box.l + caption_box.w) - l
        h = max(figure_box.t + figure_box.h, caption_box.t + caption_box.h) - t
        return [l, t, w, h]

    def _convert_to_pixel_coords(self, bbox, im_w, im_h):
        """Convert normalized coordinates to pixel coordinates."""
        crop_bbox = [bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]]
        crop_bbox = np.array(crop_bbox) * np.array([im_w, im_h, im_w, im_h])
        # Adjust for full width
        crop_bbox[0] = 0.05 * im_w
        crop_bbox[2] = 0.95 * im_w
        return [int(x) for x in crop_bbox]

    def _save_figures_metadata(self):
        """Save metadata about extracted figures."""
        metadata = {
            'figures': {k: str(v) for k, v in self.figures.items()},
            'displayed_figures': self.displayed_figures,
            'thumbnail_source': self.thumbnail_source
        }
        with open(self.data_folder / "figures_metadata.json", "w") as f:
            json.dump(metadata, f, indent=4)

    def load_figures_metadata(self):
        """Load saved figures metadata."""
        try:
            with open(self.data_folder / "figures_metadata.json", "r") as f:
                metadata = json.load(f)
                self.figures = {k: Path(v) for k, v in metadata['figures'].items()}
                self.displayed_figures = metadata['displayed_figures']
                self.thumbnail_source = metadata['thumbnail_source']
        except FileNotFoundError:
            pass

    def set_displayed_figures(self, figure_ids: List[str]):
        """Set which figures should be displayed."""
        self.displayed_figures = [fig_id for fig_id in figure_ids if fig_id in self.figures]
        self._save_figures_metadata()

    def set_thumbnail_source(self, source: str):
        """Set the source for the thumbnail image."""
        if source in ['abstract', 'full'] or source in self.figures:
            self.thumbnail_source = source
            self._save_figures_metadata()

    def create_thumbnail(self, mode='abstract'):
        """Create thumbnail from specified source."""
        if self.thumbnail_source in self.figures:
            return self.figures[self.thumbnail_source]
        else:
                # check if parsed_doc.json exists
            if (self.data_folder / "parsed_doc.json").exists():
                with open(self.data_folder / "parsed_doc.json", "r") as f:
                    doc = Document.from_json(json.load(f))
            else:
                recipe = CoreRecipe()
                doc = recipe.run(str(self.pdf_path))
                # Save the parsed doc as a JSON file
                with open(self.data_folder / "parsed_doc.json", "w") as f:
                    json.dump(doc.to_json(), f, indent=4)

            page = doc.pages[0]
            highlighted = plot_entities_on_page(page.images[0], page.tokens, box_width=0, box_alpha=0.3, box_color="yellow")
            highlighted = plot_entities_on_page(highlighted, page.abstracts, box_width=2, box_alpha=0.1, box_color="red")

            rasterizer = PDF2ImageRasterizer()
            rasterized_image = rasterizer.rasterize(str(self.pdf_path), 300)
            im_w, im_h = rasterized_image[0].pilimage.size

            abstract_bbox = page.abstracts[0].boxes[0]
            l, t, w, h = abstract_bbox.l, abstract_bbox.t, abstract_bbox.w, abstract_bbox.h

            if mode == 'full':
                # Include everything up to and including the abstract, remove margins
                l = t = 0.075
                r = 0.925
                b = t + h + 0.01
            else:
                # Just the abstract
                b = t + h + 0.01
                r = l + w

            # Convert from fractions to pixels
            bbox = [l * im_w, t * im_h, r * im_w, b * im_h]
            bbox = [int(coord) for coord in bbox]

            # Crop the image using the bounding box
            cropped_image = rasterized_image[0].pilimage.crop(bbox)
            thumbnail_path = self.data_folder / "thumbnail.png"
            cropped_image.save(thumbnail_path)

            return thumbnail_path

    # def summarize(self, summarizer: PaperSummarizer) -> str:
    #     """
    #     Generate a summary of the article using Claude.
    #     Returns the summary text with figure placeholders.
    #     """
        # summary, display_figures, thumbnail_figure = summarizer.summarize(self.data_folder)
        
        # # Update the article's displayed figures
        # self.set_displayed_figures(display_figures)
        
        # # Set the thumbnail source
        # if thumbnail_figure:
        #     self.set_thumbnail_source(thumbnail_figure)
        # else:
        #     # Default to abstract if no suitable figure
        #     self.set_thumbnail_source('abstract')
        
        # return summary
