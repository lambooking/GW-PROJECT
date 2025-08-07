#!/usr/bin/env python3
"""
快速重新索引 - 直接从extracted contents加载
"""
import json
import logging
from pathlib import Path
from src.inference.rag_knowledge_base import RAGKnowledgeBase
from src.data_processing.schemas import DocumentInfo, TextContent, Table, StandardizedDocument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_document_from_extracted_contents(data, filename):
    """从extracted contents创建StandardizedDocument"""
    try:
        # 提取文件名和基本信息
        original_filename = filename.replace("extracted_contents_", "").split("_")[0]
        doc_info_data = data.get("document_info", {})
        
        # 创建DocumentInfo
        doc_info = DocumentInfo(
            scene_type=doc_info_data.get("scene_type", "scenario_one"),
            scene_name=doc_info_data.get("scene_name", "作业指导书"),
            file_name=doc_info_data.get("file_name", original_filename),
            total_pages=doc_info_data.get("total_pages", 1),
            processing_timestamp=doc_info_data.get("processing_timestamp", "2025-08-04T00:00:00"),
            classification_confidence=doc_info_data.get("classification_confidence", 0.8)
        )
        
        # 从scoring_contents中提取文本内容
        text_contents = []
        scoring_contents = data.get("scoring_contents", {})
        
        # 处理各个评分项的内容
        for section_name, section_data in scoring_contents.items():
            if isinstance(section_data, dict) and "content" in section_data:
                content = section_data["content"]
                
                if isinstance(content, str) and content.strip():
                    # 按页面和段落分割内容
                    sections = content.split("---")
                    for i, section in enumerate(sections):
                        section = section.strip()
                        if section and len(section) > 10:  # 忽略太短的片段
                            # 尝试提取页码信息
                            page_number = 1
                            lines = section.split('\n')
                            for line in lines:
                                if line.startswith("第") and "页" in line:
                                    try:
                                        page_number = int(line.split("第")[1].split("页")[0])
                                        break
                                    except:
                                        pass
                            
                            text_content = TextContent(
                                content=section,
                                page_number=page_number,
                                section_name=section_name,
                                section_type="content",
                                hierarchy_level=0,
                                word_count=len(section.split())
                            )
                            text_contents.append(text_content)
        
        # 如果没有找到内容，尝试其他方法
        if not text_contents:
            # 尝试从原始内容中提取
            for key in ["content", "structure", "quality"]:
                if key in scoring_contents:
                    section_data = scoring_contents[key]
                    if isinstance(section_data, dict) and "content" in section_data:
                        content_str = section_data["content"]
                        if isinstance(content_str, str) and len(content_str) > 50:
                            text_content = TextContent(
                                content=content_str,
                                page_number=1,
                                section_name=key,
                                section_type="content",
                                hierarchy_level=0,
                                word_count=len(content_str.split())
                            )
                            text_contents.append(text_content)
        
        # 转换表格内容（如果有的话）
        tables = []
        
        # 创建StandardizedDocument
        document = StandardizedDocument(
            document_info=doc_info,
            text_content=text_contents,
            tables=tables,
            images=[]
        )
        
        logger.info(f"Created document with {len(text_contents)} text contents and {len(tables)} tables")
        return document
        
    except Exception as e:
        logger.error(f"Failed to create document from extracted contents: {e}")
        import traceback
        traceback.print_exc()
        return None

def quick_reindex():
    """快速重新索引"""
    
    # 1. 初始化知识库
    knowledge_base = RAGKnowledgeBase()
    logger.info("Knowledge base initialized")
    
    # 2. 查找extracted_contents中的结果
    extracted_dir = Path("output/extracted_contents")
    if not extracted_dir.exists():
        logger.error("No extracted_contents directory found")
        return
    
    success_count = 0
    for json_file in extracted_dir.glob("extracted_contents_*.json"):
        try:
            logger.info(f"Loading: {json_file}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 从extracted contents构建StandardizedDocument
            doc = create_document_from_extracted_contents(data, json_file.name)
            if doc:
                result = knowledge_base.add_document(doc)
                logger.info(f"✅ Successfully indexed: '{doc.document_info.file_name}' with {result['chunk_count']} chunks")
                success_count += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to load from {json_file}: {e}")
    
    # 3. 检查最终状态
    stats = knowledge_base.get_stats()
    logger.info(f"📊 Final stats: {stats}")
    logger.info(f"Successfully indexed {success_count} documents")
    
    # 4. 测试搜索功能
    logger.info("Testing search functionality...")
    try:
        results = knowledge_base.search("范围", top_k=5)
        logger.info(f"Search for '范围' returned {len(results)} results")
        if results:
            logger.info(f"First result: {results[0]['content'][:100]}...")
    except Exception as e:
        logger.error(f"Search test failed: {e}")

if __name__ == "__main__":
    quick_reindex()