"""
Document processing pipeline that orchestrates multiple processors.
"""

import logging
from typing import List, Optional

from .base import BaseDocumentProcessor
from .classification import DocumentClassifier
from .enhancement import ContentEnhancer
from ..schemas import StandardizedDocument
from ...core.exceptions import DocumentProcessingError


logger = logging.getLogger(__name__)


class DocumentProcessorPipeline:
    """Pipeline that applies multiple document processors in sequence."""
    
    def __init__(self, processors: Optional[List[BaseDocumentProcessor]] = None):
        """Initialize pipeline with processors."""
        if processors is None:
            # Default processing pipeline
            processors = [
                DocumentClassifier(),
                ContentEnhancer()
            ]
        
        self.processors = processors
        logger.info(f"Initialized processing pipeline with {len(processors)} processors")
    
    def process(self, document: StandardizedDocument) -> StandardizedDocument:
        """Process document through all processors in pipeline."""
        try:
            logger.info(f"Starting document processing pipeline for: {document.document_info.file_name}")
            
            processed_document = document
            
            for processor in self.processors:
                logger.debug(f"Applying processor: {processor.name}")
                processed_document = processor.process(processed_document)
            
            logger.info(f"Completed document processing pipeline for: {document.document_info.file_name}")
            return processed_document
            
        except Exception as e:
            logger.error(f"Document processing pipeline failed: {e}")
            raise DocumentProcessingError(f"Processing pipeline failed: {e}")
    
    def add_processor(self, processor: BaseDocumentProcessor) -> None:
        """Add a processor to the pipeline."""
        self.processors.append(processor)
        logger.debug(f"Added processor: {processor.name}")
    
    def remove_processor(self, processor_class: type) -> bool:
        """Remove a processor from the pipeline by class type."""
        original_length = len(self.processors)
        self.processors = [p for p in self.processors if not isinstance(p, processor_class)]
        
        removed = len(self.processors) < original_length
        if removed:
            logger.debug(f"Removed processor: {processor_class.__name__}")
        
        return removed
    
    def get_processors(self) -> List[str]:
        """Get list of processor names in pipeline."""
        return [processor.name for processor in self.processors]