from papermage.rasterizers import PDFRasterizer

PDFRasterizer().rasterize(
    "https://arxiv.org/pdf/2409.00476.pdf",
    "output.png",
)

# Will need to handle twocolumn layouts too 
import pathlib
from papermage.recipes import CoreRecipe
fixture_path = pathlib.Path(pwd).parent / "tests/fixtures"

recipe = CoreRecipe()
doc = recipe.run(fixture_path / "papermage.pdf")