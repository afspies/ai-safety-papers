import os
import requests
from pathlib import Path
from papermage.recipes import CoreRecipe
from papermage.visualizers import plot_entities_on_page
from papermage.rasterizers import PDF2ImageRasterizer

class Article:
    def __init__(self, uid, title, url):
        self.uid = uid
        self.title = title
        self.url = url
        self.data_folder = Path(f"./data/{self.uid}")
        self.data_folder.mkdir(parents=True, exist_ok=True)
        self.pdf_path = self.data_folder / "paper.pdf"

    def download_pdf(self):
        response = requests.get(self.url)
        response.raise_for_status()
        with open(self.pdf_path, 'wb') as f:
            f.write(response.content)

    def create_thumbnail(self):
        recipe = CoreRecipe()
        doc = recipe.run(str(self.pdf_path))
        page = doc.pages[0]
        highlighted = plot_entities_on_page(page.images[0], page.tokens, box_width=0, box_alpha=0.3, box_color="yellow")
        highlighted = plot_entities_on_page(highlighted, page.abstracts, box_width=2, box_alpha=0.1, box_color="red")

        rasterizer = PDF2ImageRasterizer()
        rasterized_image = rasterizer.rasterize(str(self.pdf_path), 300)
        im_w, im_h = rasterized_image[0].pilimage.size

        abstract_bbox = page.abstracts[0].boxes[0]
        l, t, w, h = abstract_bbox.l, abstract_bbox.t, abstract_bbox.w, abstract_bbox.h
        b = t + h + 0.01
        r = l + w

        bbox = [l * im_w, t * im_h, r * im_w, b * im_h]
        cropped_image = rasterized_image[0].pilimage.crop(bbox)
        thumbnail_path = self.data_folder / "thumbnail.png"
        cropped_image.save(thumbnail_path)

        return thumbnail_path
