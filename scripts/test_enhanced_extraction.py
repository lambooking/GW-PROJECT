"""
测试优化后的增强内容提取器
"""
import logging
import sys
from pathlib import Path

# 将src目录添加到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
from src.inference.enhanced_content_processor import EnhancedContentProcessor

def main():
    """
    测试优化后的增强内容提取功能
    """
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    print("🚀 开始测试优化后的增强内容提取器...")
    print("=" * 60)

    # 测试文件路径
    test_file = Path(__file__).parent.parent / "data" / "raw" / "场景1(1).pdf"
    
    if not test_file.exists():
        logger.error(f"测试文件未找到: {test_file}")
        return

    try:
        # 步骤1：运行预处理流水线
        print("📄 步骤1: 运行预处理流水线...")
        pipeline = PreprocessingPipeline()
        document = pipeline.process(str(test_file))
        print(f"✅ 预处理完成，提取了 {len(document.text_content)} 个文本段落")

        # 步骤2：运行优化后的内容提取器
        print("\n🔍 步骤2: 运行增强内容提取器...")
        processor = EnhancedContentProcessor()
        extracted_data = processor.extract_all_contents(document)

        # 步骤3：打印提取结果摘要
        print("\n📊 提取结果摘要:")
        print("=" * 60)
        
        doc_info = extracted_data["document_info"]
        print(f"📄 文档名称: {doc_info['file_name']}")
        print(f"📋 场景类型: {doc_info['scene_type']} ({doc_info['scene_name']})")
        print(f"📊 总页数: {doc_info['total_pages']}")
        print(f"🔧 处理器版本: {extracted_data['extraction_info']['processor_version']}")

        # 文档统计信息
        stats = extracted_data["document_statistics"]
        print(f"\n📈 文档统计:")
        print(f"  - 文本段落: {stats['total_text_items']}")
        print(f"  - 表格数量: {stats['total_tables']}")
        print(f"  - 图片数量: {stats['total_images']}")
        print(f"  - 总字数: {stats['total_word_count']}")

        # 章节结构
        structure = extracted_data["section_structure"]
        print(f"\n🏗️ 章节结构:")
        print(f"  - 总章节数: {structure['total_sections']}")
        if structure['missing_sections']:
            print(f"  - 缺失章节: {', '.join(structure['missing_sections'])}")

        # 各评分项提取结果
        print(f"\n🎯 各评分项提取结果:")
        scoring_contents = extracted_data["scoring_contents"]
        
        for item_key, item_data in scoring_contents.items():
            status = "✅" if item_data["extraction_success"] else "❌"
            stats = item_data.get("statistics", {})
            
            print(f"\n{status} {item_data['name']} ({item_key}):")
            if item_data["extraction_success"]:
                print(f"    📏 内容长度: {stats.get('total_length', 0)} 字符")
                print(f"    📄 覆盖页面: {stats.get('page_count', 0)} 页 {stats.get('pages_covered', [])}")
                print(f"    📝 有效行数: {stats.get('non_empty_lines', 0)}")
                
                # 显示内容预览
                content_preview = item_data["content"][:150]
                if len(item_data["content"]) > 150:
                    content_preview += "..."
                print(f"    👀 内容预览: {content_preview}")
            else:
                print(f"    ❌ 提取失败: {item_data.get('error', '未知错误')}")

        # 质量对比分析
        print(f"\n📊 质量改进分析:")
        print("=" * 60)
        
        # 元数据提取质量
        metadata_stats = scoring_contents.get("metadata", {}).get("statistics", {})
        print(f"🔍 元数据提取:")
        print(f"  - 版本信息发现: {metadata_stats.get('version_info_found', 0)} 项")
        print(f"  - 签名信息发现: {metadata_stats.get('signature_info_found', 0)} 项")
        print(f"  - 覆盖页面数: {metadata_stats.get('page_count', 0)} 页")

        # 结构完整性分析
        structure_stats = scoring_contents.get("structure", {}).get("statistics", {})
        print(f"\n🏗️ 结构完整性:")
        print(f"  - 章节标题数: {structure_stats.get('section_headers', 0)} 个")
        print(f"  - 表格发现数: {structure_stats.get('tables_found', 0)} 个")
        print(f"  - 覆盖页面数: {structure_stats.get('page_count', 0)} 页")

        # 内容完整性分析
        content_stats = scoring_contents.get("content", {}).get("statistics", {})
        print(f"\n📝 内容完整性:")
        print(f"  - 关键词匹配: {content_stats.get('keyword_matches', 0)} 个")
        print(f"  - 其他内容项: {content_stats.get('other_content_items', 0)} 个")
        print(f"  - 覆盖页面数: {content_stats.get('page_count', 0)} 页")

        # 安全和质量相关
        safety_stats = scoring_contents.get("safety", {}).get("statistics", {})
        quality_stats = scoring_contents.get("quality", {}).get("statistics", {})
        print(f"\n🛡️ 专项内容:")
        print(f"  - 安全相关内容: {safety_stats.get('keyword_matches', 0)} 个匹配")
        print(f"  - 质量相关内容: {quality_stats.get('keyword_matches', 0)} 个匹配")
        print(f"  - 技术参数内容: {scoring_contents.get('technical', {}).get('statistics', {}).get('keyword_matches', 0)} 个匹配")

        print("\n🎉 增强内容提取测试完成！")
        print("=" * 60)
        
        # 显示保存的文件信息
        print(f"💾 详细结果已保存为JSON文件")
        print(f"📁 可在 output/extracted_contents/ 目录中查看")

    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    main() 