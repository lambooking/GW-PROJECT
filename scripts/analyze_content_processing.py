"""
内容处理分析脚本，用于分析和展示文档内容是如何被处理和发送给大模型的。
"""
import json
import logging
import sys
from pathlib import Path

# 将src目录添加到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
from src.inference.enhanced_content_processor import EnhancedContentProcessor

logger = logging.getLogger(__name__)

def main():
    """
    分析文档内容处理流程。
    """
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    print("=" * 80)
    print("📊 文档内容处理分析")
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

    # 初始化增强内容处理器
    processor = EnhancedContentProcessor()

    print("\n" + "=" * 60)
    print("📈 文档基本统计信息")
    print("=" * 60)
    
    stats = processor.get_content_statistics(document)
    print(f"总页数: {stats['total_pages']}")
    print(f"文本段落数: {stats['total_text_items']}")
    print(f"表格数: {stats['total_tables']}")
    print(f"图片数: {stats['total_images']}")
    print(f"总字数: {stats['total_word_count']}")
    
    print("\n各页内容分布:")
    for page, info in sorted(stats['content_by_page'].items()):
        print(f"  第{page}页: {info['items']} 个段落, {info['words']} 字")
    
    print("\n内容类型分布:")
    for content_type, info in stats['content_types'].items():
        print(f"  {content_type}: {info['count']} 个, {info['words']} 字")

    print("\n" + "=" * 60)
    print("📋 章节结构分析")
    print("=" * 60)
    
    structure = processor.extract_section_structure(document)
    print(f"总章节数: {structure['total_sections']}")
    print(f"发现的章节: {', '.join(structure['sections_found'])}")
    if structure['missing_sections']:
        print(f"缺失的必需章节: {', '.join(structure['missing_sections'])}")
    
    print("\n按层级分组:")
    for level, sections in structure['sections_by_level'].items():
        print(f"  第{level}级: {', '.join(sections)}")

    print("\n" + "=" * 60)
    print("📝 当前内容提取方式对比")
    print("=" * 60)

    # 1. 当前元数据提取方式（前3页）
    print("\n🔍 当前元数据提取方式（前3页）:")
    metadata_summary = ""
    for item in document.text_content:
        if item.page_number <= 3:
            metadata_summary += item.content + "\n"
    
    print(f"内容长度: {len(metadata_summary)} 字符")
    print("内容预览:")
    print(metadata_summary[:300] + "..." if len(metadata_summary) > 300 else metadata_summary)

    # 2. 当前评分内容摘要方式（1000字符限制）
    print("\n🎯 当前评分内容摘要方式（1000字符限制）:")
    current_summary = ""
    current_length = 0
    for item in document.text_content:
        if current_length >= 1000:
            break
        content = item.content
        if current_length + len(content) > 1000:
            remaining = 1000 - current_length
            content = content[:remaining] + "..."
        current_summary += content + "\n"
        current_length += len(content)
    
    print(f"内容长度: {len(current_summary)} 字符")
    print("内容预览:")
    print(current_summary[:300] + "..." if len(current_summary) > 300 else current_summary)

    # 3. 增强的智能摘要方式
    print("\n🚀 增强的智能摘要方式（2000字符，智能选择）:")
    intelligent_summary = processor.generate_intelligent_summary(document, max_length=2000)
    
    print(f"内容长度: {len(intelligent_summary)} 字符")
    print("内容预览:")
    print(intelligent_summary[:300] + "..." if len(intelligent_summary) > 300 else intelligent_summary)

    print("\n" + "=" * 60)
    print("🔄 发送给大模型的内容完整性分析")
    print("=" * 60)

    total_content_length = sum(len(item.content) for item in document.text_content)
    
    print(f"文档总内容长度: {total_content_length} 字符")
    print(f"当前元数据提取覆盖率: {len(metadata_summary)/total_content_length*100:.1f}%")
    print(f"当前评分内容覆盖率: {len(current_summary)/total_content_length*100:.1f}%")
    print(f"增强摘要覆盖率: {len(intelligent_summary)/total_content_length*100:.1f}%")

    print("\n📋 改进建议:")
    print("1. 使用智能摘要算法，优先选择重要内容")
    print("2. 增加内容长度限制，减少信息丢失")
    print("3. 分段处理，针对不同评分维度使用不同内容范围")
    print("4. 引入重要性评分机制，确保关键信息不被遗漏")

    print("\n" + "=" * 80)
    print("✅ 内容处理分析完成")
    print("=" * 80)

if __name__ == "__main__":
    main()