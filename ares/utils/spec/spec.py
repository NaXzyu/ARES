"""Abstract base class for specification file builders."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

class Spec(ABC):
    """Abstract base class for building specification files from templates."""
    
    def __init__(self, output_dir: Union[str, Path], name: str):
        """Initialize the spec file builder with common parameters.
        
        Args:
            output_dir: Directory where the spec file will be written
            name: Name of the application/package
        """
        self.output_dir = Path(output_dir) if output_dir else None
        self.name = name
    
    @abstractmethod
    def apply(self, **kwargs) -> Optional[Path]:
        """Create a specification file from a template with the provided parameters.
        
        Args:
            **kwargs: Template-specific parameters
            
        Returns:
            Path to the created spec file if successful, None otherwise
        """
        pass
    
    @classmethod
    def get_template_path(cls, template_name: str) -> Path:
        """Get the path to a template file.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Path to the template file
        """
        from ares.utils.paths import Paths
        return Paths.get_spec_template(template_name)
