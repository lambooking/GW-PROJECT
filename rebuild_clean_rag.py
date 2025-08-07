#!/usr/bin/env python3
"""
重建干净的RAG知识库
"""
import logging
import shutil
from pathlib import Path
from src.inference.rag_knowledge_base import RAGKnowledgeBase
from src.data_processing.preprocessing_pipeline import PreprocessingPipeline

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def rebuild_clean_rag():
    """重建干净的RAG知识库"""
    
    print("🧹 开始重建干净的RAG知识库...")
    print("=" * 50)
    
    # 1. 清理旧的知识库
    chroma_dir = Path("chroma_db")
    if chroma_dir.exists():
        print(f"🗑️  删除旧知识库: {chroma_dir}")
        shutil.rmtree(chroma_dir)
    
    # 2. 重新初始化知识库
    print("🔄 初始化新的RAG知识库...")
    knowledge_base = RAGKnowledgeBase()
    pipeline = PreprocessingPipeline()
    
    # 3. 重新处理文档
    doc_path = "data/raw/场景1(1).pdf"
    if Path(doc_path).exists():
        print(f"📄 重新处理文档: {doc_path}")
        try:
            # 预处理文档
            document = pipeline.process(doc_path)
            print(f"✅ 文档预处理完成: {len(document.text_content)} 个文本段落")
            
            # 添加到知识库
            knowledge_base.add_document(document)
            print(f"✅ 文档已添加到知识库")
            
            # 检查结果
            stats = knowledge_base.get_stats()
            print(f"📊 知识库统计: {stats['total_documents']} 个文档, {stats['total_chunks']} 个文档块")
            
            # 测试检索
            print("\n🔍 测试检索结果:")
            test_queries = ["范围", "职责", "作业内容", "相关文件", "记录文件"]
            for query in test_queries:
                results = knowledge_base.search(query, top_k=2)
                print(f"   查询 '{query}': 找到 {len(results)} 个结果")
                if results:
                    first_result = results[0]['content'][:100].replace('\n', ' ')
                    print(f"     首个结果: {first_result}...")
            
            print("\n🎉 RAG知识库重建完成！")
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ 文档文件不存在: {doc_path}")

if __name__ == "__main__":
    rebuild_clean_rag()