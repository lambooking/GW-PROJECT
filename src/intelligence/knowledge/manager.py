"""
Knowledge base manager with support for multiple backends.
"""

import logging
from typing import Dict, List, Any, Optional

from .chromadb_kb import ChromaDBKnowledgeBase
from ...core.interfaces import KnowledgeBase
from ...core.exceptions import KnowledgeBaseError, ConfigurationError
from ...config.schemas import KnowledgeBaseConfig
from ...data.schemas import StandardizedDocument


logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """Manager for knowledge base operations with multiple backend support."""
    
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize knowledge base manager."""
        self.config = config
        self._knowledge_base: Optional[KnowledgeBase] = None
        self._initialize_backend()
    
    def _initialize_backend(self) -> None:
        """Initialize the appropriate knowledge base backend."""
        try:
            if self.config.storage_type.lower() == "chromadb":
                self._knowledge_base = ChromaDBKnowledgeBase(self.config)
            else:
                raise ConfigurationError(f"Unsupported storage type: {self.config.storage_type}")
            
            logger.info(f"Initialized {self.config.storage_type} knowledge base")
            
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to initialize knowledge base: {e}")
    
    def add_document(self, document: StandardizedDocument, metadata: Optional[Dict] = None) -> str:
        """Add document to knowledge base."""
        if not self._knowledge_base:
            raise KnowledgeBaseError("Knowledge base not initialized")
        
        try:
            doc_id = self._knowledge_base.add_document(document, metadata)
            logger.info(f"Added document to knowledge base: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to add document to knowledge base: {e}")
            raise KnowledgeBaseError(f"Failed to add document: {e}")
    
    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Query knowledge base for relevant information."""
        if not self._knowledge_base:
            raise KnowledgeBaseError("Knowledge base not initialized")
        
        try:
            results = self._knowledge_base.query(query, top_k)
            logger.debug(f"Knowledge base query returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Failed to query knowledge base: {e}")
            raise KnowledgeBaseError(f"Query failed: {e}")
    
    def get_document(self, document_id: str) -> Optional[StandardizedDocument]:
        """Retrieve document by ID."""
        if not self._knowledge_base:
            raise KnowledgeBaseError("Knowledge base not initialized")
        
        try:
            return self._knowledge_base.get_document(document_id)
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise KnowledgeBaseError(f"Failed to get document: {e}")
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in knowledge base."""
        if not self._knowledge_base:
            raise KnowledgeBaseError("Knowledge base not initialized")
        
        try:
            return self._knowledge_base.list_documents()
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise KnowledgeBaseError(f"Failed to list documents: {e}")
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document from knowledge base."""
        if not self._knowledge_base:
            raise KnowledgeBaseError("Knowledge base not initialized")
        
        try:
            if hasattr(self._knowledge_base, 'delete_document'):
                return self._knowledge_base.delete_document(document_id)
            else:
                logger.warning("Delete operation not supported by current backend")
                return False
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise KnowledgeBaseError(f"Failed to delete document: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        if not self._knowledge_base:
            return {"error": "Knowledge base not initialized"}
        
        try:
            documents = self.list_documents()
            total_docs = len(documents)
            
            stats = {
                "total_documents": total_docs,
                "storage_type": self.config.storage_type,
                "storage_path": self.config.storage_path,
                "collection_name": self.config.collection_name
            }
            
            if hasattr(self._knowledge_base, 'get_collection_stats'):
                collection_stats = self._knowledge_base.get_collection_stats()
                stats.update(collection_stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get knowledge base statistics: {e}")
            return {"error": str(e)}
    
    def rebuild_index(self) -> bool:
        """Rebuild knowledge base index."""
        if not self._knowledge_base:
            raise KnowledgeBaseError("Knowledge base not initialized")
        
        try:
            if hasattr(self._knowledge_base, 'rebuild_index'):
                return self._knowledge_base.rebuild_index()
            else:
                logger.warning("Index rebuild not supported by current backend")
                return False
        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            raise KnowledgeBaseError(f"Failed to rebuild index: {e}")
    
    def clear(self) -> bool:
        """Clear all data from knowledge base."""
        if not self._knowledge_base:
            raise KnowledgeBaseError("Knowledge base not initialized")
        
        try:
            if hasattr(self._knowledge_base, 'clear'):
                return self._knowledge_base.clear()
            else:
                logger.warning("Clear operation not supported by current backend")
                return False
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            raise KnowledgeBaseError(f"Failed to clear knowledge base: {e}")
    
    @property
    def is_initialized(self) -> bool:
        """Check if knowledge base is initialized."""
        return self._knowledge_base is not None