# %%
# helper function to get current working directory
from IPython import get_ipython # type: ignore
import os
pwd = os.path.abspath(get_ipython().run_line_magic("pwd", ""))  # type: ignore
os.path.abspath(get_ipython().run_line_magic("pwd", ""))  # type: ignore

# %%
import pathlib
from papermage.recipes import CoreRecipe
fixture_path = pathlib.Path(pwd).parent / ""

recipe = CoreRecipe()
doc = recipe.run("./paper.pdf")

# %%
from papermage.visualizers import plot_entities_on_page

page = doc.pages[0]
highlighted = plot_entities_on_page(page.images[0], page.tokens, box_width=0, box_alpha=0.3, box_color="yellow")
highlighted = plot_entities_on_page(highlighted, page.abstracts, box_width=2, box_alpha=0.1, box_color="red")
display(highlighted)

# %%


# %%
from papermage.magelib.box import Box

# %%
import numpy as np
# Get bounding box starting from top of page and going down until the end of the abstract
# Use this to crop the rasterized image using PIL
from papermage.rasterizers import PDF2ImageRasterizer

rasterizer = PDF2ImageRasterizer()
rasterized_image = rasterizer.rasterize("./paper.pdf", 300)

# rasterized_image[0].pilimage.crop((0, 0, 100, 100))
im_w, im_h = rasterized_image[0].pilimage.size
print(im_w, im_h)

get_abstract_and_title = True
abstract_bbox = page.abstracts[0].boxes[0] # bbox is (left, top, right, bottom)
print(type(abstract_bbox))
l, t, w, h = abstract_bbox.l, abstract_bbox.t, abstract_bbox.w, abstract_bbox.h

b = t + h + 0.01
r = l + w
if get_abstract_and_title:
    l = t = 0.075
    r = 0.95

# convert from fractions to pixels
bbox = np.array([l, t, r, b]) * np.array([im_w, im_h, im_w, im_h])
bbox = bbox.astype(int)


# Crop the image using the bounding box
cropped_image = rasterized_image[0].pilimage.crop(bbox)
display(cropped_image)
# save the cropped image
cropped_image.save("cropped_image.png")

# Import the Article class
from models.article import Article

# Example usage
def process_article(uid, title, url):
    article = Article(uid, title, url)
    article.download_pdf()
    thumbnail_path = article.create_thumbnail()
    print(f"Thumbnail created at: {thumbnail_path}")

# Example call
# process_article("example_uid", "Example Title", "http://example.com/paper.pdf")
