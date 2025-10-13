#!/usr/bin/env python3
"""
ChromaDB 诊断和修复脚本
检查 ChromaDB 实际数据状态并修复问题
"""
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def diagnose_chromadb():
    """诊断 ChromaDB 状态"""
    
    print("="*60)
    print("  ChromaDB 诊断工具")
    print("="*60)
    print()
    
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError:
        print("❌ ChromaDB 未安装")
        print("   安装: pip install chromadb")
        return False
    
    # 1. 检查 ChromaDB 目录
    print("1. 检查 ChromaDB 目录...")
    chromadb_path = Path("output/rag_knowledge_base/chromadb")
    
    if not chromadb_path.exists():
        print(f"   ❌ ChromaDB 目录不存在: {chromadb_path}")
        print("   这是正常的，如果这是首次运行")
        return False
    else:
        print(f"   ✅ ChromaDB 目录存在: {chromadb_path}")
    
    # 2. 连接 ChromaDB
    print("\n2. 连接 ChromaDB...")
    try:
        client = chromadb.PersistentClient(
            path=str(chromadb_path),
            settings=Settings(anonymized_telemetry=False)
        )
        print("   ✅ 连接成功")
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False
    
    # 3. 检查 Collection
    print("\n3. 检查 Collection...")
    collection_name = "intelligent_audit_kb"
    
    try:
        collection = client.get_collection(collection_name)
        print(f"   ✅ Collection 存在: {collection_name}")
    except Exception as e:
        print(f"   ❌ Collection 不存在: {e}")
        print(f"   需要创建新的 collection")
        return False
    
    # 4. 检查实际数据量
    print("\n4. 检查实际数据...")
    try:
        count = collection.count()
        print(f"   📊 ChromaDB 实际数据量: {count} 个chunks")
        
        if count == 0:
            print("   ❌ ChromaDB 中没有任何数据！")
            print("   这就是为什么查询返回空的原因")
            return False
        else:
            print(f"   ✅ ChromaDB 有数据")
            
            # 获取一些样本数据
            print("\n5. 获取样本数据...")
            try:
                sample = collection.get(limit=3, include=["documents", "metadatas", "embeddings"])
                
                if sample and sample.get("ids"):
                    print(f"   样本数量: {len(sample['ids'])}")
                    
                    for i, (doc_id, doc, metadata) in enumerate(zip(
                        sample["ids"], 
                        sample["documents"],
                        sample["metadatas"]
                    )):
                        print(f"\n   样本 {i+1}:")
                        print(f"     ID: {doc_id}")
                        print(f"     内容预览: {doc[:50]}...")
                        print(f"     页码: {metadata.get('page_number', 'N/A')}")
                        print(f"     类型: {metadata.get('chunk_type', 'N/A')}")
                    
                    # 检查 embedding 维度
                    if sample.get("embeddings") and len(sample["embeddings"]) > 0:
                        embedding_dim = len(sample["embeddings"][0])
                        print(f"\n   📏 Embedding 维度: {embedding_dim}")
                        
                        if embedding_dim != 768:
                            print(f"   ⚠️  警告：Embedding 维度不是 768！")
                            print(f"      当前维度: {embedding_dim}")
                            print(f"      期望维度: 768 (GTE中文模型)")
                            print(f"      可能需要重新索引")
                            return False
                        else:
                            print(f"   ✅ Embedding 维度正确")
                    
                    return True
                    
            except Exception as e:
                print(f"   ❌ 获取样本数据失败: {e}")
                return False
                
    except Exception as e:
        print(f"   ❌ 检查数据失败: {e}")
        return False


def test_query():
    """测试向量查询"""
    print("\n" + "="*60)
    print("  测试向量查询")
    print("="*60)
    print()
    
    try:
        from src.inference.rag_knowledge_base import RAGKnowledgeBase
        
        print("1. 初始化知识库...")
        kb = RAGKnowledgeBase()
        print("   ✅ 知识库初始化成功")
        
        # 检查统计信息
        stats = kb.get_stats()
        print(f"\n2. 知识库统计（来自元数据）:")
        print(f"   文档数: {stats['total_documents']}")
        print(f"   文档块数: {stats['total_chunks']}")
        
        # 检查 ChromaDB 实际数据
        print(f"\n3. ChromaDB 实际数据:")
        try:
            actual_count = kb.vector_storage.collection.count()
            print(f"   实际块数: {actual_count}")
            
            if actual_count != stats['total_chunks']:
                print(f"   ⚠️  不匹配！元数据显示 {stats['total_chunks']}，但ChromaDB只有 {actual_count}")
                print(f"   需要重新索引")
                return False
        except Exception as e:
            print(f"   ❌ 获取实际数据失败: {e}")
            return False
        
        # 测试查询
        print(f"\n4. 测试查询...")
        test_queries = [
            "范围",
            "职责",
            "作业内容",
            "管道",
            "安全"
        ]
        
        for query in test_queries:
            results = kb.search(query, top_k=5, min_score=0.0)  # min_score=0 不过滤
            print(f"   查询 '{query}': {len(results)} 个结果")
            
            if results and len(results) > 0:
                print(f"     最高得分: {results[0]['score']:.4f}")
                print(f"     内容预览: {results[0]['content'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    
    # 诊断 ChromaDB
    chromadb_ok = diagnose_chromadb()
    
    if chromadb_ok:
        # 如果 ChromaDB 有数据，测试查询
        query_ok = test_query()
        
        if query_ok:
            print("\n" + "="*60)
            print("✅ 诊断完成：系统正常")
            print("="*60)
            return 0
        else:
            print("\n" + "="*60)
            print("⚠️  诊断完成：查询有问题")
            print("="*60)
            print("\n建议操作：")
            print("  1. 清空 ChromaDB: rm -rf output/rag_knowledge_base/chromadb/")
            print("  2. 重新索引: python quick_reindex.py")
            return 1
    else:
        print("\n" + "="*60)
        print("❌ 诊断完成：ChromaDB 没有数据或有问题")
        print("="*60)
        print("\n建议操作：")
        print("  1. 清空所有数据:")
        print("     rm -rf output/rag_knowledge_base/")
        print("")
        print("  2. 重新索引文档:")
        print("     python quick_reindex.py")
        print("")
        print("  3. 如果没有 extracted_contents 目录，直接运行评分:")
        print("     python run_complete_rag_scoring.py score your_document.pdf")
        print("     (系统会自动将文档添加到知识库)")
        return 1


if __name__ == "__main__":
    sys.exit(main())


