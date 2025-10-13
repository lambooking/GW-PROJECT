#!/usr/bin/env python3
"""
测试余弦距离修复
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("="*60)
print("  测试余弦距离修复")
print("="*60)
print()

try:
    from src.inference.rag_knowledge_base import RAGKnowledgeBase
    from src.data_processing.schemas import StandardizedDocument, DocumentInfo, TextContent
    from datetime import datetime
    
    # 1. 初始化知识库（会创建使用余弦距离的新 collection）
    print("1. 初始化知识库（使用余弦距离）...")
    kb = RAGKnowledgeBase()
    print("   ✅ 知识库初始化完成")
    
    # 2. 创建测试文档
    print("\n2. 创建测试文档...")
    doc_info = DocumentInfo(
        file_name="test_cosine.pdf",
        file_path="/tmp/test_cosine.pdf",
        total_pages=1,
        processing_timestamp=datetime.now(),
        scene_type="scenario_one",
        scene_name="作业指导书"
    )
    
    text_content = [
        TextContent(content="1 范围", page_number=1, section_type="title", hierarchy_level=1, word_count=3),
        TextContent(content="本作业指导书适用于YQ作业区的范围管理", page_number=1, section_type="content", word_count=15),
        TextContent(content="2 职责", page_number=1, section_type="title", hierarchy_level=1, word_count=3),
        TextContent(content="作业区职责分工说明，包括各岗位职责", page_number=1, section_type="content", word_count=12),
        TextContent(content="3 作业内容", page_number=1, section_type="title", hierarchy_level=1, word_count=5),
        TextContent(content="具体作业内容和操作步骤的详细说明", page_number=1, section_type="content", word_count=12),
    ]
    
    test_doc = StandardizedDocument(
        document_info=doc_info,
        text_content=text_content,
        tables=[],
        images=[]
    )
    print("   ✅ 测试文档创建完成")
    
    # 3. 添加到知识库
    print("\n3. 添加文档到知识库...")
    result = kb.add_document(test_doc)
    print(f"   ✅ 添加完成，共 {result['chunk_count']} 个chunks")
    
    # 4. 测试查询
    print("\n4. 测试查询...")
    test_queries = [
        ("范围", 0.2),
        ("职责", 0.2),
        ("作业内容", 0.2),
    ]
    
    all_pass = True
    
    for query, min_score in test_queries:
        results = kb.search(query, top_k=5, min_score=min_score)
        print(f"\n   查询: '{query}' (min_score={min_score})")
        print(f"   返回结果: {len(results)} 个")
        
        if results:
            for i, result in enumerate(results[:3]):
                print(f"     [{i+1}] score={result['score']:.4f}, content='{result['content'][:40]}...'")
            
            # 检查最高分是否 >= min_score
            if results[0]['score'] >= min_score:
                print(f"   ✅ 相似度正常（{results[0]['score']:.4f} >= {min_score}）")
            else:
                print(f"   ❌ 相似度过低（{results[0]['score']:.4f} < {min_score}）")
                all_pass = False
        else:
            print(f"   ❌ 没有返回结果")
            all_pass = False
    
    print("\n" + "="*60)
    if all_pass:
        print("✅ 余弦距离修复成功！")
        print("\n现在可以清空知识库并重新运行评分:")
        print("  rm -rf output/rag_knowledge_base/")
        print("  python run_complete_rag_scoring.py score your_document.pdf")
    else:
        print("❌ 修复未完全成功，请检查")
    print("="*60)
    
    sys.exit(0 if all_pass else 1)
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


