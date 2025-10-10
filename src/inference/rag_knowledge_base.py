"""
RAG知识库系统
将文档内容全量存储为向量数据库，支持基于问题的动态检索
"""
import json
import logging
import hashlib
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available, using fallback vector storage")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMER_AVAILABLE = False
    logging.warning("SentenceTransformer not available, using fallback embeddings")

from ..data_processing.schemas import StandardizedDocument, TextContent, Table, Image

logger = logging.getLogger(__name__)

class DocumentChunk:
    """文档分块单元"""
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
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "chunk_type": self.chunk_type,
            "page_number": self.page_number,
            "section_name": self.section_name,
            "word_count": self.word_count,
            "metadata": self.metadata
        }

class VectorStorage:
    """向量存储抽象类"""
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        raise NotImplementedError
    
    def search(self, query_embedding: List[float], top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
        raise NotImplementedError
    
    def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        raise NotImplementedError

class ChromaDBStorage(VectorStorage):
    """基于ChromaDB的向量存储"""
    def __init__(self, collection_name: str = "document_chunks", persist_directory: str = "output/vector_db"):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is required for vector storage")
        
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"Loaded existing collection '{collection_name}' with {self.collection.count()} chunks")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Document chunks for RAG system"}
            )
            logger.info(f"Created new collection '{collection_name}'")
    
    def add_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        """添加文档块到向量数据库"""
        if not chunks:
            return
            
        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        
        # 清理元数据：ChromaDB只支持简单的键值对（str, int, float, bool），不支持None
        metadatas = []
        for chunk in chunks:
            chunk_dict = chunk.to_dict()
            clean_metadata = {}
            for key, value in chunk_dict.items():
                if value is None:
                    # ChromaDB不支持None值，跳过或设置默认值
                    if key == "section_name":
                        clean_metadata[key] = "unknown"
                    # 对于None值，我们跳过而不是添加到metadata中
                elif isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = value
                elif isinstance(value, dict):
                    # 将嵌套字典转换为JSON字符串
                    clean_metadata[key + "_json"] = str(value)
                else:
                    # 其他类型转换为字符串
                    clean_metadata[key] = str(value)
            metadatas.append(clean_metadata)
        
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        logger.info(f"Added {len(chunks)} chunks to vector database")

        # 诊断日志：验证添加操作
        try:
            count = self.collection.count()
            logger.info(f"Verification: Collection now contains {count} chunks.")
            if len(chunks) > 0:
                retrieved = self.collection.get(ids=[chunks[0].chunk_id], include=["metadatas"])
                logger.info(f"Verification: Retrieved first chunk successfully - ID: {retrieved['ids'][0]}")
        except Exception as e:
            logger.error(f"Verification failed after adding chunks: {e}")
    
    def search(self, query_embedding: List[float], top_k: int = 10) -> List[Tuple[DocumentChunk, float]]:
        """搜索相关文档块"""
        logger.info(f"ChromaDB search initiated with top_k={top_k}")
        logger.info(f"Query embedding shape: {np.array(query_embedding).shape}, first 5 values: {query_embedding[:5]}")

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []

        # 诊断日志：打印原始查询结果
        logger.info(f"ChromaDB raw query results: {results}")

        if not results or not results.get("ids") or not results["ids"][0]:
            logger.warning("ChromaDB returned empty or invalid results.")
            return []
        
        chunks_with_scores = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0], 
            results["distances"][0]
        )):
            chunk = DocumentChunk(
                chunk_id=metadata["chunk_id"],
                content=metadata["content"],
                chunk_type=metadata["chunk_type"],
                page_number=metadata["page_number"],
                section_name=metadata.get("section_name"),
                metadata=metadata.get("metadata", {})
            )
            # ChromaDB returns distance, convert to similarity score
            similarity_score = 1.0 / (1.0 + distance)
            chunks_with_scores.append((chunk, similarity_score))
        
        return chunks_with_scores
    
    def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        """获取特定文档块"""
        try:
            results = self.collection.get(ids=[chunk_id], include=["documents", "metadatas"])
            if results["documents"]:
                metadata = results["metadatas"][0]
                return DocumentChunk(
                    chunk_id=metadata["chunk_id"],
                    content=metadata["content"],
                    chunk_type=metadata["chunk_type"],
                    page_number=metadata["page_number"],
                    section_name=metadata.get("section_name"),
                    metadata=metadata.get("metadata", {})
                )
        except Exception as e:
            logger.error(f"Error retrieving chunk {chunk_id}: {e}")
        return None

class EmbeddingModel:
    """封装SentenceTransformer的嵌入模型，支持魔塔社区中文模型"""
    
    def __init__(self, 
                 model_name: str = "iic/nlp_gte_sentence-embedding_chinese-base",
                 local_model_path: str = "/home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base"):
        """
        初始化 Embedding 模型
        
        Args:
            model_name: 魔塔社区模型ID
            local_model_path: 本地模型缓存路径
        """
        self.model_name = model_name
        self.local_model_path = Path(local_model_path)
        self.model = None
        self.embedding_dim = 768  # 中文GTE模型的向量维度
        
        try:
            # 加载顺序：
            # 1. 检查本地路径是否存在
            # 2. 尝试从魔塔社区下载
            # 3. 回退到项目内models目录
            
            if self._load_from_local():
                logger.info(f"✅ 成功从本地加载模型: {self.local_model_path}")
            elif self._download_from_modelscope():
                logger.info(f"✅ 成功从魔塔社区下载模型到: {self.local_model_path}")
            else:
                raise ImportError("无法加载 Embedding 模型")
                
        except Exception as e:
            logger.error(f"❌ Embedding模型加载失败: {e}")
            logger.error("请检查:")
            logger.error("  1. 是否安装了 sentence-transformers: pip install sentence-transformers")
            logger.error("  2. 是否安装了 modelscope: pip install modelscope")
            logger.error(f"  3. 或手动下载模型到: {self.local_model_path}")
            raise ImportError(f"Embedding模型加载失败: {e}")
    
    def _load_from_local(self) -> bool:
        """从本地路径加载模型"""
        if not SENTENCE_TRANSFORMER_AVAILABLE:
            return False
        
        if self.local_model_path.exists():
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"正在从本地加载模型: {self.local_model_path}")
                self.model = SentenceTransformer(str(self.local_model_path))
                return True
            except Exception as e:
                logger.warning(f"从本地加载模型失败: {e}")
                return False
        else:
            logger.info(f"本地模型路径不存在: {self.local_model_path}")
            return False
    
    def _download_from_modelscope(self) -> bool:
        """从魔塔社区下载模型"""
        if not SENTENCE_TRANSFORMER_AVAILABLE:
            logger.error("sentence-transformers 未安装")
            return False
        
        try:
            from modelscope import snapshot_download
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"正在从魔塔社区下载模型: {self.model_name}")
            logger.info(f"下载位置: {self.local_model_path}")
            
            # 确保目录存在
            self.local_model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 从魔塔社区下载模型
            model_dir = snapshot_download(
                self.model_name,
                cache_dir=str(self.local_model_path.parent),
                revision='master'
            )
            
            logger.info(f"模型下载完成: {model_dir}")
            
            # 加载模型
            self.model = SentenceTransformer(model_dir)
            
            # 如果下载位置不是预期位置，移动文件
            if Path(model_dir) != self.local_model_path:
                import shutil
                if self.local_model_path.exists():
                    shutil.rmtree(self.local_model_path)
                shutil.move(model_dir, self.local_model_path)
                logger.info(f"模型已移动到: {self.local_model_path}")
            
            return True
            
        except ImportError as e:
            logger.error(f"modelscope 未安装或导入失败: {e}")
            logger.error("请安装: pip install modelscope")
            return False
        except Exception as e:
            logger.error(f"从魔塔社区下载模型失败: {e}")
            return False
    
    def encode(self, texts: list) -> list:
        """
        将文本转换为向量
        
        Args:
            texts: 要编码的文本列表
            
        Returns:
            向量列表
        """
        if self.model is None:
            raise RuntimeError(
                "Embedding模型未加载。请检查:\n"
                "  1. sentence-transformers 是否已安装\n"
                "  2. modelscope 是否已安装\n"
                "  3. 网络连接是否正常\n"
                f"  4. 或手动下载模型到: {self.local_model_path}"
            )
        
        try:
            # 使用真实的SentenceTransformer模型
            embeddings = self.model.encode(texts, convert_to_tensor=False, show_progress_bar=False)
            return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings
        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            raise RuntimeError(f"文本编码失败: {e}")

class DocumentChunker:
    """文档智能分块器"""
    def __init__(self, max_chunk_size: int = 500, overlap_size: int = 50):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
    
    def chunk_document(self, document: StandardizedDocument) -> List[DocumentChunk]:
        """将标准化文档分块"""
        chunks = []
        
        # 1. 处理文本内容
        chunks.extend(self._chunk_text_content(document.text_content))
        
        # 2. 处理表格
        chunks.extend(self._chunk_tables(document.tables))
        
        # 3. 处理图片（如果有OCR文本）
        chunks.extend(self._chunk_images(document.images))
        
        logger.info(f"Created {len(chunks)} chunks from document '{document.document_info.file_name}'")
        return chunks
    
    def _chunk_text_content(self, text_content: List[TextContent]) -> List[DocumentChunk]:
        """分块文本内容"""
        chunks = []
        
        for i, text_item in enumerate(text_content):
            content = text_item.content.strip()
            if not content:
                continue
            
            # 清理干扰标记
            content = self._clean_content(content)
            if not content:  # 清理后如果内容为空，跳过
                continue
            
            # 根据内容类型和长度决定分块策略
            if text_item.section_type == "title" or len(content) <= self.max_chunk_size:
                # 标题或短文本：整体作为一个chunk
                chunk_id = f"text_{i}_{self._generate_hash(content)}"
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    content=content,
                    chunk_type=text_item.section_type or "content",
                    page_number=text_item.page_number,
                    section_name=text_item.section_name,
                    metadata={
                        "hierarchy_level": text_item.hierarchy_level,
                        "word_count": text_item.word_count,
                        "original_index": i
                    }
                )
                chunks.append(chunk)
            else:
                # 长文本：按段落分块
                sub_chunks = self._split_long_text(content, i, text_item)
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _chunk_tables(self, tables: List[Table]) -> List[DocumentChunk]:
        """分块表格内容"""
        chunks = []
        
        for i, table in enumerate(tables):
            # 表格标题
            if table.caption:
                chunk_id = f"table_caption_{i}_{self._generate_hash(table.caption)}"
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    content=f"表格标题：{table.caption}",
                    chunk_type="table_caption",
                    page_number=table.page_number,
                    metadata={
                        "table_id": table.table_id,
                        "table_type": table.table_type,
                        "original_index": i
                    }
                )
                chunks.append(chunk)
            
            # 表格内容（转换为文本）
            table_text = self._table_to_text(table)
            if table_text:
                chunk_id = f"table_content_{i}_{self._generate_hash(table_text)}"
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    content=table_text,
                    chunk_type="table",
                    page_number=table.page_number,
                    metadata={
                        "table_id": table.table_id,
                        "table_type": table.table_type,
                        "headers": table.headers,
                        "row_count": len(table.data),
                        "original_index": i
                    }
                )
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_images(self, images: List[Image]) -> List[DocumentChunk]:
        """分块图片内容（主要是OCR文本）"""
        chunks = []
        
        for i, image in enumerate(images):
            if image.extracted_text and image.extracted_text.strip():
                chunk_id = f"image_text_{i}_{self._generate_hash(image.extracted_text)}"
                content = f"图片描述：{image.description or '无描述'}\nOCR文本：{image.extracted_text}"
                
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    content=content,
                    chunk_type="image",
                    page_number=image.page_number,
                    metadata={
                        "image_id": image.image_id,
                        "image_type": image.type,
                        "description": image.description,
                        "original_index": i
                    }
                )
                chunks.append(chunk)
        
        return chunks
    
    def _split_long_text(self, text: str, index: int, text_item: TextContent) -> List[DocumentChunk]:
        """分割长文本"""
        chunks = []
        sentences = text.split('。')  # 按句号分割
        
        current_chunk = ""
        chunk_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) <= self.max_chunk_size:
                current_chunk += sentence + "。"
            else:
                # 创建当前chunk
                if current_chunk:
                    chunk_id = f"text_{index}_{chunk_count}_{self._generate_hash(current_chunk)}"
                    chunk = DocumentChunk(
                        chunk_id=chunk_id,
                        content=current_chunk.strip(),
                        chunk_type=text_item.section_type or "content",
                        page_number=text_item.page_number,
                        section_name=text_item.section_name,
                        metadata={
                            "hierarchy_level": text_item.hierarchy_level,
                            "original_index": index,
                            "sub_chunk": chunk_count
                        }
                    )
                    chunks.append(chunk)
                    chunk_count += 1
                
                # 开始新chunk
                current_chunk = sentence + "。"
        
        # 添加最后一个chunk
        if current_chunk:
            chunk_id = f"text_{index}_{chunk_count}_{self._generate_hash(current_chunk)}"
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                content=current_chunk.strip(),
                chunk_type=text_item.section_type or "content",
                page_number=text_item.page_number,
                section_name=text_item.section_name,
                metadata={
                    "hierarchy_level": text_item.hierarchy_level,
                    "original_index": index,
                    "sub_chunk": chunk_count
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _table_to_text(self, table: Table) -> str:
        """将表格转换为文本描述"""
        if not table.headers and not table.data:
            return ""
        
        lines = []
        
        # 添加表头
        if table.headers:
            lines.append("表头：" + " | ".join(table.headers))
        
        # 添加数据行（最多前10行）
        if table.data:
            lines.append("表格数据：")
            for i, row in enumerate(table.data[:10]):  # 限制行数
                if len(row) == len(table.headers or []):
                    row_text = " | ".join(str(cell) for cell in row)
                    lines.append(f"第{i+1}行：{row_text}")
                else:
                    lines.append(f"第{i+1}行：{' | '.join(str(cell) for cell in row)}")
            
            if len(table.data) > 10:
                lines.append(f"... (共{len(table.data)}行数据)")
        
        return "\n".join(lines)
    
    def _clean_content(self, content: str) -> str:
        """清理内容中的干扰标记"""
        import re
        
        # 移除 === xxx === 格式的分隔符
        content = re.sub(r'=== .* ===', '', content)
        
        # 移除页码标记（如：第X页: 、[第X页] 等）
        content = re.sub(r'第\d+页\s*:', '', content)
        content = re.sub(r'\[第\d+页\]', '', content)
        
        # 移除内部处理标记（如：[grammar]、[unknown]等）
        content = re.sub(r'\[(grammar|unknown|safety|content|structure|metadata)\]', '', content)
        
        # 移除多余的空白行
        content = re.sub(r'\n\s*\n', '\n', content)
        
        # 清理首尾空白
        content = content.strip()
        
        return content
    
    def _generate_hash(self, text: str) -> str:
        """生成文本的短哈希"""
        return hashlib.md5(text.encode()).hexdigest()[:8]

class RAGKnowledgeBase:
    """RAG知识库主类"""
    def __init__(self, 
                 collection_name: str = "intelligent_audit_kb",
                 persist_directory: str = "output/rag_knowledge_base",
                 use_chromadb: bool = True):
        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.embedding_model = EmbeddingModel()
        self.chunker = DocumentChunker()
        
        # 初始化向量存储
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is required for RAG system. Please install it with 'pip install chromadb'")

        self.vector_storage = ChromaDBStorage(
            collection_name=collection_name,
            persist_directory=str(self.persist_directory / "chromadb")
        )

        # 文档注册表
        self.document_registry_path = self.persist_directory / "document_registry.json"
        self.document_registry = self._load_document_registry()
    
    def _load_document_registry(self) -> Dict[str, Any]:
        """加载文档注册表"""
        if self.document_registry_path.exists():
            try:
                with open(self.document_registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading document registry: {e}")
        return {}
    
    def _save_document_registry(self):
        """保存文档注册表"""
        try:
            with open(self.document_registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.document_registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving document registry: {e}")
    
    def add_document(self, document: StandardizedDocument) -> Dict[str, Any]:
        """添加文档到知识库"""
        doc_name = document.document_info.file_name
        doc_hash = self._calculate_document_hash(document)
        
        # 检查文档是否已存在
        if doc_name in self.document_registry:
            if self.document_registry[doc_name]["document_hash"] == doc_hash:
                logger.info(f"Document '{doc_name}' already exists with same content, skipping")
                return self.document_registry[doc_name]
            else:
                logger.info(f"Document '{doc_name}' exists but content changed, updating")
        
        logger.info(f"Adding document '{doc_name}' to knowledge base...")
        
        # 1. 文档分块
        chunks = self.chunker.chunk_document(document)
        
        # 2. 生成嵌入向量
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_model.encode(chunk_texts)

        # 诊断日志：检查生成的向量
        if embeddings:
            first_embedding = embeddings[0]
            logger.info(f"Generated {len(embeddings)} embeddings.")
            logger.info(f"First embedding shape: {np.array(first_embedding).shape}, first 5 values: {first_embedding[:5]}")
        else:
            logger.warning("Embedding model returned no embeddings.")

        # 3. 存储到向量数据库
        self.vector_storage.add_chunks(chunks, embeddings)
        
        # 4. 更新文档注册表
        doc_info = {
            "file_name": doc_name,
            "document_hash": doc_hash,
            "added_timestamp": datetime.now().isoformat(),
            "scene_type": document.document_info.scene_type,
            "scene_name": document.document_info.scene_name,
            "total_pages": document.document_info.total_pages,
            "chunk_count": len(chunks),
            "chunk_types": {
                chunk_type: len([c for c in chunks if c.chunk_type == chunk_type])
                for chunk_type in set(chunk.chunk_type for chunk in chunks)
            }
        }
        
        self.document_registry[doc_name] = doc_info
        self._save_document_registry()
        
        logger.info(f"Successfully added document '{doc_name}' with {len(chunks)} chunks")
        return doc_info
    
    def search(self, query: str, top_k: int = 10, min_score: float = 0.3) -> List[Dict[str, Any]]:
        """搜索相关内容"""
        logger.info(f"Searching for: {query}")
        
        # 1. 生成查询向量
        query_embedding = self.embedding_model.encode([query])[0]
        
        # 2. 向量搜索
        results = self.vector_storage.search(query_embedding, top_k=top_k * 2)  # 多检索一些以便过滤

        # 增加详细日志，用于调试
        if results:
            top_scores = [f"{score:.4f}" for _, score in results[:5]]
            logger.info(f"Top 5 raw scores from vector storage: {top_scores}")
        else:
            logger.warning("Vector storage returned no results.")

        # 3. 过滤和格式化结果
        formatted_results = []
        for chunk, score in results:
            if score >= min_score:
                result = {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "chunk_type": chunk.chunk_type,
                    "page_number": chunk.page_number,
                    "section_name": chunk.section_name,
                    "score": score,
                    "metadata": chunk.metadata
                }
                formatted_results.append(result)
        
        # 4. 限制返回数量
        formatted_results = formatted_results[:top_k]
        
        logger.info(f"Found {len(formatted_results)} relevant chunks (score >= {min_score})")
        return formatted_results
    
    def get_context_for_question(self, question: str, max_context_length: int = 2000) -> str:
        """为特定问题获取上下文"""
        results = self.search(question, top_k=20, min_score=0.2)
        
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result["content"]
            page_info = f"[第{result['page_number']}页]"
            
            if result["section_name"]:
                section_info = f"[{result['section_name']}]"
                full_content = f"{page_info}{section_info} {content}"
            else:
                full_content = f"{page_info} {content}"
            
            if current_length + len(full_content) <= max_context_length:
                context_parts.append(full_content)
                current_length += len(full_content)
            else:
                break
        
        context = "\n\n".join(context_parts)
        logger.info(f"Generated context with {len(context_parts)} chunks, total length: {len(context)}")
        return context
    
    def _calculate_document_hash(self, document: StandardizedDocument) -> str:
        """计算文档内容哈希"""
        content_str = f"{document.document_info.file_name}_{document.document_info.total_pages}"
        content_str += "".join([text.content for text in document.text_content])
        content_str += "".join([str(table.data) for table in document.tables])
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return {
            "total_documents": len(self.document_registry),
            "documents": list(self.document_registry.keys()),
            "total_chunks": sum(doc["chunk_count"] for doc in self.document_registry.values()),
            "storage_type": type(self.vector_storage).__name__,
            "embedding_model": self.embedding_model.model_name
        } 