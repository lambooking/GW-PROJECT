"""
Base document processor for post-processing operations.
"""

import logging
from abc import abstractmethod

from ...core.interfaces import DocumentProcessor
from ..schemas import StandardizedDocument


logger = logging.getLogger(__name__)


class BaseDocumentProcessor(DocumentProcessor):
    """Base implementation for document processors."""
    
    def __init__(self):
        """Initialize processor."""
        self.name = self.__class__.__name__
    
    def process(self, document: StandardizedDocument) -> StandardizedDocument:
        """Process a standardized document."""
        try:
            logger.debug(f"Processing document with {self.name}")
            processed_document = self._process_document(document)
            logger.debug(f"Completed processing with {self.name}")
            return processed_document
        except Exception as e:
            logger.error(f"Processing failed in {self.name}: {e}")
            raise
    
    @abstractmethod
    def _process_document(self, document: StandardizedDocument) -> StandardizedDocument:
        """Internal processing implementation."""
        pass