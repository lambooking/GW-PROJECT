"""
ChromaDB-based knowledge base implementation.
"""

import json
import logging
import hashlib
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMER_AVAILABLE = False

from ...core.interfaces import KnowledgeBase
from ...core.exceptions import KnowledgeBaseError, ConfigurationError
from ...config.schemas import KnowledgeBaseConfig
from ...data.schemas import StandardizedDocument, TextContent, Table, Image


logger = logging.getLogger(__name__)


class DocumentChunk:
    """Document chunk unit for storage in knowledge base."""
    
    def __init__(self, 
                 chunk_id: str,
                 content: str,
                 chunk_type: str,
                 page_number: int,
                 section_name: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.chunk_id = chunk_id
        self.content = content
        self.chunk_type = chunk_type  # text, table, image, title
        self.page_number = page_number
        self.section_name = section_name
        self.metadata = metadata or {}
        self.word_count = len(content.split())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "chunk_type": self.chunk_type,
            "page_number": self.page_number,
            "section_name": self.section_name,
            "metadata": self.metadata,
            "word_count": self.word_count
        }


class ChromaDBKnowledgeBase(KnowledgeBase):
    """ChromaDB-based knowledge base for document storage and retrieval."""
    
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize ChromaDB knowledge base."""
        if not CHROMADB_AVAILABLE:
            raise ConfigurationError("ChromaDB not available. Install with: pip install chromadb")
        
        self.config = config
        self._embedding_model: Optional[SentenceTransformer] = None
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection = None
        self._document_registry: Dict[str, Dict[str, Any]] = {}
        self._fallback_storage: Dict[str, StandardizedDocument] = {}
        
        self._initialize_chromadb()
        self._initialize_embedding_model()
        self._load_document_registry()
    
    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            storage_path = Path(self.config.storage_path)
            storage_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB client
            self._client = chromadb.PersistentClient(
                path=str(storage_path / "chromadb"),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"ChromaDB initialized at {storage_path}")
            
        except Exception as e:
            raise KnowledgeBaseError(f"Failed to initialize ChromaDB: {e}")
    
    def _initialize_embedding_model(self) -> None:
        """Initialize sentence transformer model for embeddings."""
        try:
            if SENTENCE_TRANSFORMER_AVAILABLE:
                # 优先使用本地模型，避免网络下载
                model_path = Path("models") / self.config.embedding_model
                if model_path.exists():
                    logger.info(f"使用本地嵌入模型: {model_path}")
                    self._embedding_model = SentenceTransformer(str(model_path), device='cuda')
                else:
                    logger.info(f"本地模型不存在，使用预训练模型: {self.config.embedding_model}")
                    # 避免自动下载，使用缓存模型
                    try:
                        self._embedding_model = SentenceTransformer(self.config.embedding_model, device='cuda')
                    except Exception:
                        logger.warning("无法加载预训练模型，禁用嵌入功能")
                        self._embedding_model = None
                        return
                
                logger.info(f"✅ 嵌入模型已加载: {self.config.embedding_model}")
            else:
                logger.warning("SentenceTransformer不可用，使用回退方案")
                self._embedding_model = None
                
        except Exception as e:
            logger.warning(f"嵌入模型加载失败，将使用ChromaDB默认嵌入: {e}")
            self._embedding_model = None
    
    def _load_document_registry(self) -> None:
        """Load document registry from disk."""
        try:
            registry_file = Path(self.config.storage_path) / "document_registry.json"
            fallback_file = Path(self.config.storage_path) / "fallback_storage.pkl"
            
            if registry_file.exists():
                with open(registry_file, 'r', encoding='utf-8') as f:
                    self._document_registry = json.load(f)
            
            if fallback_file.exists():
                with open(fallback_file, 'rb') as f:
                    self._fallback_storage = pickle.load(f)
            
            logger.debug(f"Loaded {len(self._document_registry)} documents from registry")
            
        except Exception as e:
            logger.warning(f"Failed to load document registry: {e}")
            self._document_registry = {}
            self._fallback_storage = {}
    
    def _save_document_registry(self) -> None:
        """Save document registry to disk."""
        try:
            storage_path = Path(self.config.storage_path)
            registry_file = storage_path / "document_registry.json"
            fallback_file = storage_path / "fallback_storage.pkl"
            
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(self._document_registry, f, ensure_ascii=False, indent=2, default=str)
            
            with open(fallback_file, 'wb') as f:
                pickle.dump(self._fallback_storage, f)
                
        except Exception as e:
            logger.error(f"Failed to save document registry: {e}")
    
    def add_document(self, document: StandardizedDocument, metadata: Optional[Dict] = None) -> str:
        """Add document to knowledge base."""
        try:
            # Generate document ID
            doc_id = self._generate_document_id(document)
            
            # Check if document already exists
            if doc_id in self._document_registry:
                logger.info(f"Document {doc_id} already exists, skipping")
                return doc_id
            
            # Process document into chunks
            chunks = self._process_document_to_chunks(document, doc_id)
            
            if not chunks:
                logger.warning(f"No chunks generated for document {doc_id}")
                return doc_id
            
            # Store chunks in ChromaDB
            self._store_chunks(chunks)
            
            # Update registry
            self._document_registry[doc_id] = {
                "document_id": doc_id,
                "file_name": document.document_info.file_name,
                "file_path": document.document_info.file_path,
                "scene_type": document.document_info.scene_type,
                "total_pages": document.document_info.total_pages,
                "chunk_count": len(chunks),
                "added_timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store full document in fallback storage
            self._fallback_storage[doc_id] = document
            
            # Save to disk
            self._save_document_registry()
            
            logger.info(f"Added document {doc_id} with {len(chunks)} chunks")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise KnowledgeBaseError(f"Failed to add document: {e}")
    
    def _generate_document_id(self, document: StandardizedDocument) -> str:
        """Generate unique document ID."""
        content_hash = hashlib.md5(
            f"{document.document_info.file_name}_{document.get_full_text()[:1000]}".encode()
        ).hexdigest()[:12]
        return f"doc_{content_hash}"
    
    def _process_document_to_chunks(self, document: StandardizedDocument, doc_id: str) -> List[DocumentChunk]:
        """Process document into chunks for storage."""
        chunks = []
        chunk_counter = 0
        
        # Process text content
        for text_content in document.text_content:
            chunk_text = text_content.content.strip()
            if len(chunk_text) < 10:  # Skip very short content
                continue
            
            # Split long content into smaller chunks
            if len(chunk_text) > self.config.chunk_size:
                sub_chunks = self._split_text_to_chunks(chunk_text)
                for i, sub_chunk in enumerate(sub_chunks):
                    chunk = DocumentChunk(
                        chunk_id=f"{doc_id}_chunk_{chunk_counter}",
                        content=sub_chunk,
                        chunk_type="text",
                        page_number=text_content.page_number,
                        section_name=text_content.section_name,
                        metadata={
                            "document_id": doc_id,
                            "section_type": text_content.section_type,
                            "hierarchy_level": text_content.hierarchy_level,
                            "sub_chunk_index": i
                        }
                    )
                    chunks.append(chunk)
                    chunk_counter += 1
            else:
                chunk = DocumentChunk(
                    chunk_id=f"{doc_id}_chunk_{chunk_counter}",
                    content=chunk_text,
                    chunk_type="text",
                    page_number=text_content.page_number,
                    section_name=text_content.section_name,
                    metadata={
                        "document_id": doc_id,
                        "section_type": text_content.section_type,
                        "hierarchy_level": text_content.hierarchy_level
                    }
                )
                chunks.append(chunk)
                chunk_counter += 1
        
        # Process tables
        for table in document.tables:
            table_text = self._table_to_text(table)
            if table_text:
                chunk = DocumentChunk(
                    chunk_id=f"{doc_id}_chunk_{chunk_counter}",
                    content=table_text,
                    chunk_type="table",
                    page_number=table.page_number,
                    metadata={
                        "document_id": doc_id,
                        "table_id": table.table_id,
                        "caption": table.caption
                    }
                )
                chunks.append(chunk)
                chunk_counter += 1
        
        # Process images (OCR text)
        for image in document.images:
            if image.extracted_text and len(image.extracted_text.strip()) > 10:
                chunk = DocumentChunk(
                    chunk_id=f"{doc_id}_chunk_{chunk_counter}",
                    content=image.extracted_text,
                    chunk_type="image",
                    page_number=image.page_number,
                    metadata={
                        "document_id": doc_id,
                        "image_id": image.image_id,
                        "description": image.description
                    }
                )
                chunks.append(chunk)
                chunk_counter += 1
        
        return chunks
    
    def _split_text_to_chunks(self, text: str) -> List[str]:
        """Split long text into chunks with overlap."""
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                # Find a good break point (sentence end or paragraph break)
                for i in range(end, start + chunk_size // 2, -1):
                    if text[i] in '。！？\n':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, start + 1)
            if start >= len(text):
                break
        
        return chunks
    
    def _table_to_text(self, table: Table) -> str:
        """Convert table to text representation."""
        text_parts = []
        
        if table.caption:
            text_parts.append(f"表格: {table.caption}")
        
        if table.headers:
            text_parts.append("表头: " + " | ".join(table.headers))
        
        for i, row in enumerate(table.data):
            text_parts.append(f"行{i+1}: " + " | ".join(str(cell) for cell in row))
        
        return "\n".join(text_parts)
    
    def _store_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Store chunks in ChromaDB."""
        if not chunks:
            return
        
        documents = []
        embeddings = []
        ids = []
        metadatas = []
        
        for chunk in chunks:
            documents.append(chunk.content)
            ids.append(chunk.chunk_id)
            metadatas.append(chunk.to_dict())
            
            # Generate embedding
            if self._embedding_model:
                embedding = self._embedding_model.encode(chunk.content)
                embeddings.append(embedding.tolist())
        
        # Add to collection
        if embeddings:
            self._collection.add(
                documents=documents,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas
            )
        else:
            # Fallback without custom embeddings
            self._collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
    
    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Query knowledge base for relevant information."""
        try:
            if self._embedding_model:
                query_embedding = self._embedding_model.encode(query)
                results = self._collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=top_k
                )
            else:
                results = self._collection.query(
                    query_texts=[query],
                    n_results=top_k
                )
            
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    result = {
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else 0.0
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def get_document(self, document_id: str) -> Optional[StandardizedDocument]:
        """Retrieve document by ID."""
        return self._fallback_storage.get(document_id)
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in knowledge base."""
        return list(self._document_registry.values())
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            count = self._collection.count()
            return {
                "total_chunks": count,
                "embedding_model": self.config.embedding_model,
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": self.config.chunk_overlap
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    def clear(self) -> bool:
        """Clear all data from knowledge base."""
        try:
            # Delete and recreate collection
            self._client.delete_collection(self.config.collection_name)
            self._collection = self._client.create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Clear registries
            self._document_registry.clear()
            self._fallback_storage.clear()
            self._save_document_registry()
            
            logger.info("Knowledge base cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document from knowledge base."""
        try:
            if document_id not in self._document_registry:
                return False
            
            # Find and delete chunks
            chunk_ids = []
            results = self._collection.get(where={"document_id": document_id})
            if results['ids']:
                chunk_ids = results['ids']
                self._collection.delete(ids=chunk_ids)
            
            # Remove from registries
            del self._document_registry[document_id]
            if document_id in self._fallback_storage:
                del self._fallback_storage[document_id]
            
            self._save_document_registry()
            
            logger.info(f"Deleted document {document_id} with {len(chunk_ids)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False