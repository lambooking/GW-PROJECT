"""
Base document parser with common functionality.
"""

import logging
from abc import abstractmethod
from pathlib import Path
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.interfaces import DocumentParser
    from ..schemas import StandardizedDocument

from ...core.exceptions import DocumentProcessingError


logger = logging.getLogger(__name__)


class BaseDocumentParser:
    """Base implementation for document parsers."""
    
    def __init__(self, enable_ocr: bool = True, enable_images: bool = True):
        """Initialize parser with common settings."""
        self.enable_ocr = enable_ocr
        self.enable_images = enable_images
        
    def parse(self, file_path: Union[str, Path]) -> 'StandardizedDocument':
        """Parse document file into StandardizedDocument."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise DocumentProcessingError(f"File not found: {file_path}")
        
        if not self.supports_format(file_path):
            raise DocumentProcessingError(f"Unsupported file format: {file_path.suffix}")
        
        try:
            logger.info(f"Starting to parse document: {file_path}")
            document = self._parse_document(file_path)
            logger.info(f"Successfully parsed document: {file_path}")
            return document
        except Exception as e:
            logger.error(f"Failed to parse document {file_path}: {e}")
            raise DocumentProcessingError(f"Parsing failed: {e}")
    
    @abstractmethod
    def _parse_document(self, file_path: Path) -> 'StandardizedDocument':
        """Internal parsing implementation."""
        pass
    
    def _get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes."""
        return file_path.stat().st_size
    
    def _validate_file_size(self, file_path: Path, max_size_mb: int = 50) -> None:
        """Validate file size."""
        file_size = self._get_file_size(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise DocumentProcessingError(
                f"File too large: {file_size / 1024 / 1024:.1f}MB, max allowed: {max_size_mb}MB"
            )