"""
测试批注定位改进效果
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference.rag_scoring_engine import RAGScoringEngine
from src.inference.rag_knowledge_base import RAGKnowledgeBase
from src.inference.vllm_client import VLLMInferenceClient
from src.data_processing.document_processor import DocumentProcessor

def test_annotation_location():
    """测试批注定位功能"""
    
    print("=" * 60)
    print("测试批注定位改进")
    print("=" * 60)
    
    # 1. 初始化组件
    print("\n1. 初始化组件...")
    vllm_client = VLLMInferenceClient()
    knowledge_base = RAGKnowledgeBase()
    scoring_engine = RAGScoringEngine(vllm_client, knowledge_base)
    
    # 2. 处理文档
    print("\n2. 处理测试文档...")
    test_file = "data/raw/场景1/test_document.pdf"
    
    if not Path(test_file).exists():
        print(f"❌ 测试文件不存在: {test_file}")
        print("请使用你自己的测试文档路径")
        return
    
    processor = DocumentProcessor()
    document = processor.process_document(test_file)
    
    print(f"✅ 文档处理完成: {document.document_info.file_name}")
    print(f"   总页数: {document.document_info.total_pages}")
    print(f"   文本块: {len(document.text_content)}")
    
    # 3. 执行评分
    print("\n3. 执行RAG评分...")
    result = scoring_engine.score_document(document)
    
    # 4. 检查批注位置信息
    print("\n4. 检查批注位置信息:")
    print("-" * 60)
    
    annotations = result.get("annotations", [])
    print(f"生成批注数量: {len(annotations)}")
    
    for i, ann in enumerate(annotations[:5], 1):  # 只显示前5条
        print(f"\n批注 {i}:")
        print(f"  评分项: {ann['score_item']}")
        print(f"  位置描述: {ann['location']}")
        print(f"  页码: {ann['page_number']}")
        print(f"  章节: {ann.get('section_name', '无')}")
        print(f"  坐标: {ann.get('coordinates', '无')}")
        print(f"  文本片段: {ann.get('text_snippet', '')[:50]}...")
        
        # ✅ 关键验证：位置信息是否准确
        if ann['page_number'] > 1:
            print("  ✅ 页码信息正常")
        if ann.get('section_name'):
            print(f"  ✅ 章节信息: {ann['section_name']}")
        if ann.get('text_snippet'):
            print("  ✅ 文本片段存在，可用于精确定位")
    
    # 5. 验证位置信息传递链
    print("\n5. 验证位置信息传递链:")
    print("-" * 60)
    
    detailed_scores = result.get("detailed_scores", {})
    
    for criterion_key, score_result in list(detailed_scores.items())[:3]:
        print(f"\n评分项: {score_result['name']}")
        
        location_info = score_result.get("location_info")
        if location_info:
            print("  ✅ location_info 存在")
            
            primary_chunk = location_info.get("primary_chunk")
            if primary_chunk:
                print(f"  ✅ primary_chunk:")
                print(f"     - 页码: {primary_chunk.get('page_number')}")
                print(f"     - 章节: {primary_chunk.get('section_name', '无')}")
                print(f"     - 内容片段: {primary_chunk.get('content', '')[:50]}...")
            
            page_numbers = location_info.get("page_numbers", [])
            if page_numbers:
                print(f"  ✅ 涉及页码: {page_numbers}")
        else:
            print("  ❌ location_info 缺失")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    # 返回结果供进一步分析
    return result

if __name__ == "__main__":
    result = test_annotation_location()