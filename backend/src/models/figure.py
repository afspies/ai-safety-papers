from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import logging
from abc import ABC, abstractmethod
import json
import os
import shutil

logger = logging.getLogger(__name__)

class Figure:
    """Base class representing a figure with its metadata."""
    
    def __init__(
        self, 
        id: str, 
        caption: str = "", 
        has_subfigures: bool = False,
        subfigures: List[Dict[str, Any]] = None,
        type: str = "figure",
        path: Optional[Path] = None
    ):
        self.id = id
        self.caption = caption
        self.has_subfigures = has_subfigures
        self.subfigures = subfigures or []
        self.type = type
        self.path = path
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert figure to dictionary representation."""
        return {
            "id": self.id,
            "caption": self.caption,
            "has_subfigures": self.has_subfigures,
            "subfigures": self.subfigures,
            "type": self.type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], base_path: Optional[Path] = None) -> 'Figure':
        """Create figure from dictionary representation."""
        figure = cls(
            id=data["id"],
            caption=data.get("caption", ""),
            has_subfigures=data.get("has_subfigures", False),
            subfigures=data.get("subfigures", []),
            type=data.get("type", "figure")
        )
        
        # Set path if base_path is provided and figure file exists
        if base_path:
            figure_path = base_path / f"{figure.id}.png"
            if figure_path.exists():
                figure.path = figure_path
        
        return figure
    
    def save_to_directory(self, output_dir: Path) -> Path:
        """
        Save figure image to the specified directory.
        
        Returns:
            Path to the saved figure.
        """
        if not self.path:
            raise ValueError(f"Figure {self.id} has no associated image path")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self.id}.png"
        
        shutil.copy2(self.path, output_path)
        
        # If there are subfigures, save them too
        if self.has_subfigures and self.subfigures:
            for subfig in self.subfigures:
                subfig_id = subfig.get("id")
                if not subfig_id:
                    continue
                    
                subfig_path = Path(str(self.path).replace(f"{self.id}.png", f"{self.id}_{subfig_id}.png"))
                if subfig_path.exists():
                    shutil.copy2(subfig_path, output_dir / f"{self.id}_{subfig_id}.png")
        
        return output_path


class FigureExtractor(ABC):
    """Abstract base class for figure extraction."""
    
    @abstractmethod
    def extract_figures(self, source_path: Path, output_dir: Path) -> List[Figure]:
        """
        Extract figures from the given source and save to output directory.
        
        Args:
            source_path: Path to the source (HTML, PDF, etc.)
            output_dir: Directory to save extracted figures
            
        Returns:
            List of Figure objects
        """
        pass
    
    def save_metadata(self, figures: List[Figure], output_dir: Path) -> Path:
        """
        Save figure metadata to a JSON file.
        
        Args:
            figures: List of Figure objects
            output_dir: Directory to save metadata
            
        Returns:
            Path to the metadata file
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = output_dir / "figures_metadata.json"
        
        # Convert figures to dictionary format with ID as key
        metadata = {fig.id: fig.to_dict() for fig in figures}
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        return metadata_path
    
    @staticmethod
    def load_metadata(metadata_path: Path, base_path: Optional[Path] = None) -> Dict[str, Figure]:
        """
        Load figure metadata from a JSON file.
        
        Args:
            metadata_path: Path to the metadata JSON file
            base_path: Base path for figure images
            
        Returns:
            Dictionary of figure IDs to Figure objects
        """
        if not metadata_path.exists():
            logger.warning(f"Metadata file not found: {metadata_path}")
            return {}
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_dict = json.load(f)
            
            figures = {}
            for fig_id, fig_data in metadata_dict.items():
                fig_data["id"] = fig_id  # Ensure ID is set correctly
                figures[fig_id] = Figure.from_dict(fig_data, base_path)
            
            return figures
        except Exception as e:
            logger.error(f"Error loading figure metadata: {e}")
            return {}