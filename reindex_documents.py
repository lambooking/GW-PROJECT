#!/usr/bin/env python3
"""
重新索引现有文档到ChromaDB
"""
import json
import logging
from pathlib import Path
from src.inference.rag_knowledge_base import RAGKnowledgeBase
from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
from src.data_processing.schemas import StandardizedDocument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reindex_documents():
    """重新索引文档"""
    
    # 1. 初始化组件
    knowledge_base = RAGKnowledgeBase()
    pipeline = PreprocessingPipeline()
    logger.info("Components initialized")
    
    # 2. 查找原始PDF文件并重新处理
    data_dir = Path("data/raw")
    pdf_files = []
    
    if data_dir.exists():
        for pdf_file in data_dir.glob("*.pdf"):
            pdf_files.append(pdf_file)
            logger.info(f"Found PDF document: {pdf_file}")
    
    if not pdf_files:
        logger.warning("No PDF documents found in data/raw/")
        # 尝试使用现有的处理结果
        return try_load_from_existing_results(knowledge_base)
    
    # 3. 重新处理并索引每个文档
    for pdf_file in pdf_files:
        try:
            logger.info(f"Processing and indexing: {pdf_file}")
            
            # 处理文档
            document = pipeline.process(str(pdf_file))
            
            # 添加到知识库
            result = knowledge_base.add_document(document)
            logger.info(f"✅ Successfully indexed '{document.document_info.file_name}' with {result['chunk_count']} chunks")
            
        except Exception as e:
            logger.error(f"❌ Failed to process {pdf_file}: {e}")
    
    # 4. 检查最终状态
    stats = knowledge_base.get_stats()
    logger.info(f"📊 Final stats: {stats}")

def try_load_from_existing_results(knowledge_base):
    """尝试从现有处理结果加载文档"""
    logger.info("Trying to load from existing processing results...")
    
    # 查找extracted_contents中的结果
    extracted_dir = Path("output/extracted_contents")
    if extracted_dir.exists():
        for json_file in extracted_dir.glob("extracted_contents_*.json"):
            try:
                logger.info(f"Attempting to load: {json_file}")
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 尝试从extracted contents构建StandardizedDocument
                doc = create_document_from_extracted_contents(data, json_file.name)
                if doc:
                    result = knowledge_base.add_document(doc)
                    logger.info(f"✅ Successfully indexed from extracted contents: '{doc.document_info.file_name}' with {result['chunk_count']} chunks")
                
            except Exception as e:
                logger.error(f"❌ Failed to load from {json_file}: {e}")

def create_document_from_extracted_contents(data, filename):
    """从extracted contents创建StandardizedDocument"""
    try:
        from src.data_processing.schemas import DocumentInfo, TextContent, Table, Image
        
        # 提取文件名和基本信息
        original_filename = filename.replace("extracted_contents_", "").split("_")[0]
        
        # 创建DocumentInfo
        doc_info = DocumentInfo(
            scene_type="scenario_one",  # 默认场景
            scene_name="作业指导书",
            file_name=original_filename,
            total_pages=data.get("total_pages", 1),
            processing_timestamp=data.get("processing_timestamp", "2025-08-04T00:00:00"),
            classification_confidence=0.8
        )
        
        # 转换文本内容
        text_contents = []
        for i, text_item in enumerate(data.get("text_content", [])):
            if isinstance(text_item, dict) and text_item.get("content"):
                text_content = TextContent(
                    content=text_item["content"],
                    page_number=text_item.get("page_number", 1),
                    section_name=text_item.get("section_name"),
                    section_type=text_item.get("section_type", "content"),
                    hierarchy_level=text_item.get("hierarchy_level", 0),
                    word_count=len(text_item["content"].split())
                )
                text_contents.append(text_content)
        
        # 转换表格内容
        tables = []
        for table_item in data.get("tables", []):
            if isinstance(table_item, dict):
                table = Table(
                    table_id=table_item.get("table_id", f"table_{len(tables)}"),
                    caption=table_item.get("caption", ""),
                    headers=table_item.get("headers", []),
                    data=table_item.get("data", []),
                    page_number=table_item.get("page_number", 1),
                    table_type=table_item.get("table_type", "data")
                )
                tables.append(table)
        
        # 创建StandardizedDocument
        document = StandardizedDocument(
            document_info=doc_info,
            text_content=text_contents,
            tables=tables,
            images=[]  # 暂时忽略图片
        )
        
        return document
        
    except Exception as e:
        logger.error(f"Failed to create document from extracted contents: {e}")
        return None

if __name__ == "__main__":
    reindex_documents()