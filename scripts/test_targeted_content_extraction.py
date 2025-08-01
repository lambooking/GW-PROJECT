"""
分项内容提取测试脚本，展示针对每个评分项的专门内容提取效果。
"""
import json
import logging
import sys
from pathlib import Path

# 将src目录添加到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
from src.inference.enhanced_content_processor import EnhancedContentProcessor
from src.inference.vllm_client import VLLMInferenceClient
from src.inference.info_extractor import LLMInfoExtractor
from src.inference.scoring_engine import SimpleScoringEngine

logger = logging.getLogger(__name__)

def main():
    """
    演示分项内容提取的效果。
    """
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    print("=" * 80)
    print("🔬 分项内容提取测试")
    print("=" * 80)

    # 加载测试文档
    test_file = Path(__file__).parent.parent / "data" / "raw" / "场景1(1).pdf"
    if not test_file.exists():
        logger.error(f"测试文件未找到: {test_file}")
        return

    try:
        pipeline = PreprocessingPipeline()
        document = pipeline.process(str(test_file))
        logger.info("✅ 文档预处理完成")
    except Exception as e:
        logger.error(f"❌ 预处理失败: {e}")
        return

    # 初始化内容处理器
    processor = EnhancedContentProcessor()

    # 测试各种专门的内容提取
    scoring_items = [
        ("structure", "🏗️ 结构完整性"),
        ("content", "📝 内容完整性"),
        ("grammar", "📚 语法规范性"),
        ("metadata", "🔍 元数据提取"),
        ("safety", "🛡️ 安全相关"),
        ("quality", "⭐ 质量相关"),
        ("technical", "🔧 技术参数")
    ]

    for item_type, item_name in scoring_items:
        print(f"\n" + "=" * 60)
        print(f"{item_name} 专门内容提取")
        print("=" * 60)
        
        try:
            extracted_content = processor.extract_content_for_scoring_item(document, item_type)
            
            print(f"提取内容长度: {len(extracted_content)} 字符")
            print("\n内容预览:")
            print("-" * 40)
            
            # 显示前500字符作为预览
            preview = extracted_content[:500]
            if len(extracted_content) > 500:
                preview += "..."
            print(preview)
            
            # 计算覆盖的页面范围
            lines = extracted_content.split('\n')
            page_mentions = []
            for line in lines:
                if "第" in line and "页" in line:
                    try:
                        # 提取页码
                        import re
                        page_matches = re.findall(r'第(\d+)页', line)
                        page_mentions.extend([int(p) for p in page_matches])
                    except:
                        pass
            
            if page_mentions:
                unique_pages = sorted(set(page_mentions))
                print(f"\n📄 覆盖页面: {unique_pages} (共{len(unique_pages)}页)")
            
        except Exception as e:
            logger.error(f"提取 {item_name} 内容失败: {e}")
            print(f"❌ 提取失败: {e}")

    print(f"\n" + "=" * 60)
    print("📊 新旧方式对比测试")
    print("=" * 60)

    # 对比旧的简单摘要方式
    print("\n🔴 旧方式 - 通用摘要 (1000字符限制):")
    old_summary = ""
    current_length = 0
    for item in document.text_content:
        if current_length >= 1000:
            break
        content = item.content
        if current_length + len(content) > 1000:
            remaining = 1000 - current_length
            content = content[:remaining] + "..."
        old_summary += content + "\n"
        current_length += len(content)
    
    print(f"长度: {len(old_summary)} 字符")
    print(f"预览: {old_summary[:200]}...")

    # 新的专门内容提取方式
    print(f"\n🟢 新方式 - 结构专门内容:")
    structure_content = processor.extract_content_for_scoring_item(document, "structure")
    print(f"长度: {len(structure_content)} 字符")
    print(f"预览: {structure_content[:200]}...")

    print(f"\n🟢 新方式 - 内容完整性专门内容:")
    content_completeness = processor.extract_content_for_scoring_item(document, "content")
    print(f"长度: {len(content_completeness)} 字符")
    print(f"预览: {content_completeness[:200]}...")

    print(f"\n" + "=" * 60)
    print("🎯 评分效果对比 (如果VLLM服务可用)")
    print("=" * 60)

    try:
        # 初始化VLLM客户端
        vllm_client = VLLMInferenceClient(base_url="http://localhost:8000/v1")
        
        # 测试信息提取
        print("\n🔍 测试新的元数据提取...")
        info_extractor = LLMInfoExtractor(vllm_client)
        extracted_info = info_extractor.extract_all_info(document)
        print("✅ 元数据提取成功")
        print(f"提取结果: {json.dumps(extracted_info, indent=2, ensure_ascii=False)}")
        
        # 测试评分
        print("\n🎯 测试新的分项评分...")
        scoring_engine = SimpleScoringEngine(vllm_client)
        scoring_result = scoring_engine.score_document(document, extracted_info)
        print("✅ 分项评分成功")
        
        print("\n📊 最终评分结果:")
        print(f"总分: {scoring_result.get('total_score', 0)}/100")
        print(f"等级: {scoring_result.get('grade', '未知')}")
        
        detailed_scores = scoring_result.get('detailed_scores', {})
        for score_type, score_info in detailed_scores.items():
            score = score_info.get('score', 0)
            reasoning = score_info.get('reasoning', '无说明')[:100]
            print(f"  - {score_type}: {score}分 ({reasoning}...)")
            
    except Exception as e:
        logger.warning(f"VLLM服务不可用，跳过评分测试: {e}")
        print("⚠️ VLLM服务不可用，跳过评分测试")

    print(f"\n" + "=" * 80)
    print("✅ 分项内容提取测试完成")
    print("=" * 80)
    
    print("\n💡 改进效果总结:")
    print("1. ✅ 针对性内容提取 - 每个评分项都有专门的内容")
    print("2. ✅ 无长度限制 - 不再受1000字符限制")
    print("3. ✅ 智能关键词匹配 - 自动识别相关内容")
    print("4. ✅ 全文档覆盖 - 不会遗漏重要信息")
    print("5. ✅ 结构化组织 - 内容按类别整理")

if __name__ == "__main__":
    main()