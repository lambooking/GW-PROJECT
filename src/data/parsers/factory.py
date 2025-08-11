"""
Document parser factory for creating appropriate parsers.
"""

import logging
from pathlib import Path
from typing import Dict, Type, Union

from .base import BaseDocumentParser
from .pdf_parser import PDFDocumentParser
from .docx_parser import DocxDocumentParser
from ...core.exceptions import DocumentProcessingError


logger = logging.getLogger(__name__)


class DocumentParserFactory:
    """Factory for creating document parsers based on file format."""
    
    _parsers: Dict[str, Type[BaseDocumentParser]] = {
        '.pdf': PDFDocumentParser,
        '.docx': DocxDocumentParser,
        '.doc': DocxDocumentParser,  # Treat .doc as .docx for now
    }
    
    @classmethod
    def create_parser(
        cls, 
        file_path: Union[str, Path],
        enable_ocr: bool = True,
        enable_images: bool = True
    ) -> BaseDocumentParser:
        """Create appropriate parser for the given file."""
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        if file_extension not in cls._parsers:
            raise DocumentProcessingError(
                f"Unsupported file format: {file_extension}. "
                f"Supported formats: {list(cls._parsers.keys())}"
            )
        
        parser_class = cls._parsers[file_extension]
        
        try:
            parser = parser_class(
                enable_ocr=enable_ocr,
                enable_images=enable_images
            )
            logger.debug(f"Created parser {parser_class.__name__} for {file_path}")
            return parser
        except Exception as e:
            raise DocumentProcessingError(f"Failed to create parser for {file_path}: {e}")
    
    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """Get list of supported file formats."""
        return list(cls._parsers.keys())
    
    @classmethod
    def register_parser(cls, extension: str, parser_class: Type[BaseDocumentParser]) -> None:
        """Register a new parser for a file extension."""
        extension = extension.lower()
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        cls._parsers[extension] = parser_class
        logger.info(f"Registered parser {parser_class.__name__} for extension {extension}")
    
    @classmethod
    def is_supported(cls, file_path: Union[str, Path]) -> bool:
        """Check if file format is supported."""
        file_path = Path(file_path)
        return file_path.suffix.lower() in cls._parsers