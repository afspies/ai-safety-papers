import os
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from src.utils.ar5iv_figure_processor import Ar5ivFigureProcessor

TEST_DATA_DIR = Path(__file__).parent / "test_data"

def read_test_html(filename: str) -> str:
    """Read test HTML file."""
    with open(TEST_DATA_DIR / filename, 'r', encoding='utf-8') as f:
        return f.read()

def test_single_figure():
    """Test processing of a single figure."""
    html = read_test_html('single_figure.html')
    soup = BeautifulSoup(html, 'html.parser')
    figure_elem = soup.find('figure')
    
    processor = Ar5ivFigureProcessor()
    output_dir = TEST_DATA_DIR / "output"
    output_dir.mkdir(exist_ok=True)
    
    result = processor._process_element(figure_elem, 1, output_dir)
    assert result is not None
    elem_id, figure_data = result
    
    assert elem_id == "fig1"
    assert figure_data.type == "figure"
    assert not figure_data.has_subfigures
    assert "Overview. We train Sparse Autoencoders" in figure_data.caption

def test_subfigures():
    """Test processing of figures with subfigures."""
    html = read_test_html('subfigures.html')
    soup = BeautifulSoup(html, 'html.parser')
    figure_elem = soup.find('figure')
    
    processor = Ar5ivFigureProcessor()
    output_dir = TEST_DATA_DIR / "output"
    output_dir.mkdir(exist_ok=True)
    
    result = processor._process_element(figure_elem, 2, output_dir)
    assert result is not None
    elem_id, figure_data = result
    
    assert elem_id == "fig2"
    assert figure_data.type == "figure"
    assert figure_data.has_subfigures
    assert len(figure_data.subfigures) == 2
    assert figure_data.subfigures[0]['caption'] == "(a)"
    assert figure_data.subfigures[1]['caption'] == "(b)"
    assert "Specificity plot" in figure_data.caption

# Create test data directory and files
TEST_DATA_DIR.mkdir(exist_ok=True)

# Single figure test data
single_figure_html = '''
<figure id="S1.F1" class="ltx_figure"><img src="/html/2406.17759/assets/x1.png" id="S1.F1.g1" class="ltx_graphics ltx_centering ltx_img_landscape" width="461" height="293" alt="Refer to caption">
<figcaption class="ltx_caption ltx_centering"><span class="ltx_tag ltx_tag_figure"><span id="S1.F1.4.2.1" class="ltx_text" style="font-size:90%;">Figure 1</span>: </span><span id="S1.F1.2.1" class="ltx_text" style="font-size:90%;">Overview. We train Sparse Autoencoders (SAEs) on <math>...</math></span></figcaption>
</figure>
'''

# Subfigures test data
subfigures_html = '''
<figure id="S3.F2" class="ltx_figure">
<div class="ltx_flex_figure">
<div class="ltx_flex_cell ltx_flex_size_2">
<figure id="S3.F2.sf1" class="ltx_figure ltx_figure_panel ltx_align_center"><img src="/html/2406.17759/assets/x2.png" id="S3.F2.sf1.g1" class="ltx_graphics ltx_centering ltx_img_landscape" width="461" height="346" alt="Refer to caption">
<figcaption class="ltx_caption ltx_centering"><span class="ltx_tag ltx_tag_figure"><span id="S3.F2.sf1.2.1.1" class="ltx_text" style="font-size:90%;">(a)</span> </span></figcaption>
</figure>
</div>
<div class="ltx_flex_cell ltx_flex_size_2">
<figure id="S3.F2.sf2" class="ltx_figure ltx_figure_panel ltx_align_center"><img src="/html/2406.17759/assets/x3.png" id="S3.F2.sf2.g1" class="ltx_graphics ltx_centering ltx_img_landscape" width="461" height="346" alt="Refer to caption">
<figcaption class="ltx_caption ltx_centering"><span class="ltx_tag ltx_tag_figure"><span id="S3.F2.sf2.2.1.1" class="ltx_text" style="font-size:90%;">(b)</span> </span></figcaption>
</figure>
</div>
</div>
<figcaption class="ltx_caption ltx_centering"><span class="ltx_tag ltx_tag_figure"><span id="S3.F2.2.1.1" class="ltx_text" style="font-size:90%;">Figure 2</span>: </span><span id="S3.F2.3.2" class="ltx_text" style="font-size:90%;">Specificity plot...</span></figcaption>
</figure>
'''

with open(TEST_DATA_DIR / "single_figure.html", 'w', encoding='utf-8') as f:
    f.write(single_figure_html)

with open(TEST_DATA_DIR / "subfigures.html", 'w', encoding='utf-8') as f:
    f.write(subfigures_html) 