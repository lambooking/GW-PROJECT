"""
Knowledge base management for RAG system.
"""

from .manager import KnowledgeBaseManager
from .chromadb_kb import ChromaDBKnowledgeBase

__all__ = [
    'KnowledgeBaseManager',
    'ChromaDBKnowledgeBase'
]