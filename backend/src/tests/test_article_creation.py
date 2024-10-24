import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.models.article import Article


# Test paper:
# Mechanistic Unlearning: Robust Knowledge Unlearning and Editing via Mechanistic Localization	16/10/2024	This work investigates how mechanistic interpretability -- which, in part, aims to identify model components associated to specific interpretable mechanisms that make up a model capability -- can improve the precision and effectiveness of editing and unlearning.	https://www.semanticscholar.org/paper/23a921483746b8b3c828bd601f54d485bec32014	P. Guo, Aaquib Syed, Abhay Sheshadri, Aidan Ewart, G. Dziugaite	Methods for knowledge editing and unlearning in large language models seek to edit or remove undesirable knowledge or capabilities without compromising general language modeling performance. This work investigates how mechanistic interpretability -- which, in part, aims to identify model components (circuits) associated to specific interpretable mechanisms that make up a model capability -- can improve the precision and effectiveness of editing and unlearning. We find a stark difference in unlearning and edit robustness when training components localized by different methods. We highlight an important distinction between methods that localize components based primarily on preserving outputs, and those finding high level mechanisms with predictable intermediate states. In particular, localizing edits/unlearning to components associated with the lookup-table mechanism for factual recall 1) leads to more robust edits/unlearning across different input/output formats, and 2) resists attempts to relearn the unwanted information, while also reducing unintended side effects compared to baselines, on both a sports facts dataset and the CounterFact dataset across multiple models. We also find that certain localized edits disrupt the latent knowledge in the model more than any other baselines, making unlearning more robust to various attacks.		FALSE	FALSE		2024	23a921483746b8b3c828bd601f54d485bec32014	0	1	specter_v1										

def test_article_creation():
    # Example entry data
    uid = "23a921483746b8b3c828bd601f54d485bec32014"
    title = "Methods for knowledge editing and unlearning in large language models"
    url = "https://www.semanticscholar.org/paper/23a921483746b8b3c828bd601f54d485bec32014.pdf"  # Replace with the actual URL of the PDF

    # Create an Article instance
    article = Article(uid, title, url)

    # Download the PDF
    try:
        article.download_pdf()
        print(f"PDF downloaded successfully for article: {title}")
    except Exception as e:
        print(f"Failed to download PDF: {e}")

    # Create a thumbnail
    try:
        thumbnail_path = article.create_thumbnail()
        print(f"Thumbnail created at: {thumbnail_path}")
    except Exception as e:
        print(f"Failed to create thumbnail: {e}")

if __name__ == "__main__":
    test_article_creation()
