#!/usr/bin/env python3
"""
诊断实际评分流程中的问题
"""
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def diagnose_scoring():
    """诊断评分流程"""
    
    print("="*60)
    print("  诊断评分流程问题")
    print("="*60)
    print()
    
    try:
        from src.inference.rag_knowledge_base import RAGKnowledgeBase
        from src.data_processing.schemas import StandardizedDocument, DocumentInfo, TextContent
        from datetime import datetime
        
        # 1. 创建测试文档
        print("1. 创建测试文档...")
        doc_info = DocumentInfo(
            file_name="test_scoring.pdf",
            file_path="/tmp/test_scoring.pdf",
            total_pages=1,
            processing_timestamp=datetime.now(),
            scene_type="scenario_one",
            scene_name="作业指导书"
        )
        
        # 创建包含关键词的文本内容
        text_content = [
            TextContent(content="1 范围", page_number=1, section_type="title", hierarchy_level=1, word_count=3),
            TextContent(content="本作业指导书适用范围说明", page_number=1, section_type="content", word_count=10),
            TextContent(content="2 职责", page_number=1, section_type="title", hierarchy_level=1, word_count=3),
            TextContent(content="各岗位职责分工详细说明", page_number=1, section_type="content", word_count=10),
            TextContent(content="3 作业内容", page_number=1, section_type="title", hierarchy_level=1, word_count=5),
            TextContent(content="具体作业内容和操作步骤", page_number=1, section_type="content", word_count=10),
            TextContent(content="4 相关文件", page_number=1, section_type="title", hierarchy_level=1, word_count=5),
            TextContent(content="相关参考文件列表", page_number=1, section_type="content", word_count=8),
            TextContent(content="5 记录文件", page_number=1, section_type="title", hierarchy_level=1, word_count=5),
            TextContent(content="需要记录的文件清单", page_number=1, section_type="content", word_count=8),
        ]
        
        test_doc = StandardizedDocument(
            document_info=doc_info,
            text_content=text_content,
            tables=[],
            images=[]
        )
        print("   ✅ 测试文档创建完成")
        
        # 2. 初始化知识库并添加文档
        print("\n2. 初始化知识库...")
        kb = RAGKnowledgeBase()
        
        # 检查初始状态
        init_count = kb.vector_storage.collection.count()
        print(f"   初始数据量: {init_count}")
        
        print("\n3. 添加文档到知识库...")
        result = kb.add_document(test_doc)
        print(f"   文档块数: {result['chunk_count']}")
        
        # 验证数据
        actual_count = kb.vector_storage.collection.count()
        print(f"   ChromaDB 实际数据量: {actual_count}")
        
        if actual_count == 0:
            print("   ❌ 数据没有写入！")
            return False
        
        print("   ✅ 数据写入成功")
        
        # 3. 测试各种查询
        print("\n4. 测试查询（模拟评分流程）...")
        
        # 测试查询列表（来自 rag_scoring_engine.py）
        test_queries = [
            ("范围", "结构完整性查询"),
            ("职责", "结构完整性查询"),
            ("作业内容", "结构完整性查询"),
            ("作业内容 操作步骤 具体要求", "内容完整性查询"),
            ("职责分工 责任划分 岗位职责", "内容完整性查询"),
        ]
        
        all_success = True
        
        for query, desc in test_queries:
            print(f"\n   测试查询: '{query}' ({desc})")
            
            # 使用不同的 min_score 测试
            for min_score in [0.0, 0.2, 0.3]:
                results = kb.search(query, top_k=10, min_score=min_score)
                print(f"     min_score={min_score}: {len(results)} 个结果", end="")
                
                if results:
                    top_score = results[0]['score']
                    print(f", 最高分={top_score:.4f}")
                    if min_score == 0.0:
                        print(f"       内容: {results[0]['content'][:40]}...")
                else:
                    print(" (空)")
                    if min_score == 0.0:
                        all_success = False
        
        # 4. 深度检查 - 直接用 ChromaDB API
        print("\n5. 深度检查 - 使用 ChromaDB 原始 API...")
        
        # 获取所有数据
        all_data = kb.vector_storage.collection.get(include=["documents", "metadatas", "embeddings"])
        print(f"   总数据量: {len(all_data['ids'])}")
        
        if all_data['ids']:
            print(f"   样本数据:")
            for i in range(min(3, len(all_data['ids']))):
                print(f"     [{i+1}] ID: {all_data['ids'][i]}")
                print(f"         内容: {all_data['documents'][i][:50]}...")
                print(f"         类型: {all_data['metadatas'][i].get('chunk_type', 'N/A')}")
                if all_data['embeddings']:
                    print(f"         向量维度: {len(all_data['embeddings'][i])}")
        
        # 测试原始查询
        print(f"\n6. 测试原始 ChromaDB 查询...")
        test_query = "范围"
        query_embedding = kb.embedding_model.encode([test_query])[0]
        
        print(f"   查询: '{test_query}'")
        print(f"   查询向量维度: {len(query_embedding)}")
        print(f"   查询向量前5个值: {query_embedding[:5]}")
        
        # 直接查询
        raw_results = kb.vector_storage.collection.query(
            query_embeddings=[query_embedding],
            n_results=5,
            include=["documents", "distances"]
        )
        
        print(f"\n   原始查询结果:")
        print(f"     返回数量: {len(raw_results['ids'][0]) if raw_results['ids'] else 0}")
        
        if raw_results['ids'] and raw_results['ids'][0]:
            for i, (doc_id, doc, distance) in enumerate(zip(
                raw_results['ids'][0],
                raw_results['documents'][0],
                raw_results['distances'][0]
            )):
                similarity = 1.0 / (1.0 + distance)
                print(f"     [{i+1}] ID: {doc_id}")
                print(f"         距离: {distance:.4f}, 相似度: {similarity:.4f}")
                print(f"         内容: {doc[:50]}...")
        else:
            print("     ❌ 没有返回结果！")
            all_success = False
        
        # 7. 检查向量维度一致性
        print(f"\n7. 检查向量维度...")
        
        if all_data['embeddings']:
            stored_dim = len(all_data['embeddings'][0])
            query_dim = len(query_embedding)
            
            print(f"   存储的向量维度: {stored_dim}")
            print(f"   查询向量维度: {query_dim}")
            
            if stored_dim != query_dim:
                print(f"   ❌ 向量维度不匹配！")
                all_success = False
            else:
                print(f"   ✅ 向量维度匹配")
        
        return all_success
        
    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    # 确保从干净状态开始
    import shutil
    kb_path = Path("output/rag_knowledge_base")
    if kb_path.exists():
        print("清理旧数据...")
        try:
            shutil.rmtree(kb_path)
        except:
            pass
    
    success = diagnose_scoring()
    
    print("\n" + "="*60)
    if success:
        print("✅ 诊断完成：评分流程正常")
        print("\n建议：")
        print("  如果评分还是0，可能是 min_score 阈值太高")
        print("  或者查询关键词不匹配")
    else:
        print("❌ 诊断完成：发现问题")
        print("\n请将完整输出发送以便分析")
    print("="*60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())



