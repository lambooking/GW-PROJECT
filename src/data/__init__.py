"""
Data processing layer for the RAG Scoring System.
"""

from .schemas import (
    DocumentInfo,
    TextContent,
    Table,
    Image,
    StandardizedDocument,
    ScoringResult,
    ScoreItem
)
from .parsers import DocumentParserFactory
from .processors import DocumentProcessorPipeline

__all__ = [
    'DocumentInfo',
    'TextContent',
    'Table', 
    'Image',
    'StandardizedDocument',
    'ScoringResult',
    'ScoreItem',
    'DocumentParserFactory',
    'DocumentProcessorPipeline'
]