#!/usr/bin/env python3
"""
验证 ChromaDB search 方法的 bug
"""
import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_bug():
    """验证 bug"""
    
    print("="*60)
    print("  验证 ChromaDB search 方法 bug")
    print("="*60)
    print()
    
    try:
        from src.inference.rag_knowledge_base import RAGKnowledgeBase
        import chromadb
        
        # 初始化知识库
        print("1. 连接知识库...")
        kb = RAGKnowledgeBase()
        
        # 检查数据
        count = kb.vector_storage.collection.count()
        print(f"   数据量: {count}")
        
        if count == 0:
            print("   ❌ 知识库为空，请先运行评分添加数据")
            return False
        
        # 直接用 ChromaDB API 查询
        print("\n2. 使用 ChromaDB 原始 API 查询...")
        
        test_query = "范围"
        query_embedding = kb.embedding_model.encode([test_query])[0]
        
        print(f"   查询词: '{test_query}'")
        
        # 原始查询
        raw_results = kb.vector_storage.collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"\n3. ChromaDB 原始返回结果:")
        print(f"   results.keys() = {raw_results.keys()}")
        print(f"   results['ids'] = {raw_results.get('ids')}")
        print(f"   results['documents'][0] 数量 = {len(raw_results['documents'][0]) if raw_results.get('documents') else 0}")
        print(f"   results['metadatas'][0] 数量 = {len(raw_results['metadatas'][0]) if raw_results.get('metadatas') else 0}")
        
        # 检查第一个结果的详细内容
        if raw_results['ids'] and raw_results['ids'][0]:
            print(f"\n4. 第一个结果的详细内容:")
            
            chunk_id = raw_results['ids'][0][0]
            document = raw_results['documents'][0][0]
            metadata = raw_results['metadatas'][0][0]
            distance = raw_results['distances'][0][0]
            
            print(f"\n   从 results['ids'][0][0] 读取:")
            print(f"     chunk_id = '{chunk_id}'")
            
            print(f"\n   从 results['documents'][0][0] 读取:")
            print(f"     content = '{document[:100]}...'")
            
            print(f"\n   从 results['metadatas'][0][0] 读取:")
            print(f"     metadata.keys() = {metadata.keys()}")
            print(f"     metadata['chunk_id'] = '{metadata.get('chunk_id', 'N/A')}'")
            print(f"     metadata['content'] = '{metadata.get('content', 'N/A')[:50] if metadata.get('content') else 'N/A'}...'")
            print(f"     metadata['chunk_type'] = '{metadata.get('chunk_type', 'N/A')}'")
            print(f"     metadata['page_number'] = {metadata.get('page_number', 'N/A')}")
            
            print(f"\n   从 results['distances'][0][0] 读取:")
            print(f"     distance = {distance}")
            
            # 关键验证
            print(f"\n5. 关键验证:")
            
            if 'content' in metadata:
                print(f"   ✅ metadata 包含 'content' 字段")
                print(f"      内容: '{metadata['content'][:100]}...'")
            else:
                print(f"   ❌ metadata 不包含 'content' 字段！")
                print(f"      这就是 bug 的原因！")
                print(f"      content 应该从 results['documents'][0][i] 读取")
            
            if 'chunk_id' in metadata:
                print(f"   ✅ metadata 包含 'chunk_id' 字段")
            else:
                print(f"   ❌ metadata 不包含 'chunk_id' 字段！")
                print(f"      chunk_id 应该从 results['ids'][0][i] 读取")
            
            # 对比两种读取方式
            print(f"\n6. 对比两种数据读取方式:")
            print(f"\n   正确方式（应该使用）:")
            print(f"     chunk_id = results['ids'][0][i]")
            print(f"     content = results['documents'][0][i]")
            print(f"     metadata = results['metadatas'][0][i]")
            
            print(f"\n   当前代码（错误）:")
            print(f"     chunk_id = metadata['chunk_id']")
            print(f"     content = metadata['content']")
            
            # 验证当前代码会发生什么
            print(f"\n7. 模拟当前代码的执行:")
            try:
                test_chunk_id = metadata["chunk_id"]
                test_content = metadata["content"]
                print(f"   ✅ 当前代码能执行（可能返回错误数据）")
                print(f"      读取到的 chunk_id: {test_chunk_id}")
                print(f"      读取到的 content: {test_content[:50]}...")
            except KeyError as e:
                print(f"   ❌ 当前代码会报错: KeyError: {e}")
                print(f"      这导致 search 方法返回空列表！")
                return True  # 确认了 bug
        
        # 测试实际的 search 方法
        print(f"\n8. 测试实际的 kb.search() 方法:")
        try:
            results = kb.search("范围", top_k=3, min_score=0.0)
            print(f"   返回结果数量: {len(results)}")
            
            if results:
                print(f"   ✅ search 方法返回了结果")
                for i, result in enumerate(results[:3]):
                    print(f"     [{i+1}] score={result['score']:.4f}, content={result['content'][:30]}...")
            else:
                print(f"   ❌ search 方法返回空列表")
                print(f"      这证实了 bug 的存在！")
                return True  # 确认了 bug
        except Exception as e:
            print(f"   ❌ search 方法报错: {e}")
            import traceback
            traceback.print_exc()
            return True  # 确认了 bug
        
        return False  # 没有发现 bug
        
    except Exception as e:
        print(f"\n❌ 验证过程失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    bug_confirmed = verify_bug()
    
    print("\n" + "="*60)
    if bug_confirmed:
        print("✅ Bug 已确认！")
        print("\n问题:")
        print("  ChromaDBStorage.search() 方法从 metadata 读取 'content'")
        print("  但 ChromaDB 不会在 metadata 中存储 content")
        print("  content 应该从 results['documents'] 读取")
        print("\n修复方案:")
        print("  修改 src/inference/rag_knowledge_base.py")
        print("  第 166-177 行的 search 方法")
    else:
        print("❌ 未能确认 bug，可能是其他问题")
    print("="*60)
    
    return 0 if bug_confirmed else 1


if __name__ == "__main__":
    sys.exit(main())

