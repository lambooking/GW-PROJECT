"""
测试分项内容提取和保存功能的脚本。
"""
import logging
import sys
from pathlib import Path

# 将src目录添加到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.data_processing.preprocessing_pipeline import PreprocessingPipeline

def main():
    """
    测试文档预处理时自动保存分项内容提取结果。
    """
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    print("=" * 80)
    print("🧪 测试分项内容提取和自动保存功能")
    print("=" * 80)

    # 测试文件路径
    test_file = Path(__file__).parent.parent / "data" / "raw" / "场景1(1).pdf"
    
    if not test_file.exists():
        print(f"❌ 测试文件未找到: {test_file}")
        return

    print(f"📄 测试文件: {test_file.name}")
    
    try:
        # 运行预处理流水线（现在会自动保存分项内容）
        pipeline = PreprocessingPipeline()
        standardized_doc = pipeline.process(str(test_file))
        
        print(f"\n✅ 预处理完成！")
        print(f"📊 文档信息:")
        print(f"  - 场景类型: {standardized_doc.document_info.scene_type}")
        print(f"  - 场景名称: {standardized_doc.document_info.scene_name}")
        print(f"  - 总页数: {standardized_doc.document_info.total_pages}")
        print(f"  - 文本段落数: {len(standardized_doc.text_content)}")
        print(f"  - 表格数: {len(standardized_doc.tables)}")
        print(f"  - 图片数: {len(standardized_doc.images)}")
        
        # 查看输出目录
        output_dir = Path(__file__).parent.parent / "output" / "extracted_contents"
        if output_dir.exists():
            json_files = list(output_dir.glob("*.json"))
            if json_files:
                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                print(f"\n💾 最新的分项内容文件: {latest_file.name}")
                print(f"📁 文件大小: {latest_file.stat().st_size / 1024:.1f} KB")
                print(f"🕒 创建时间: {latest_file.stat().st_mtime}")
                
                # 简单验证JSON文件内容
                import json
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    print(f"\n📋 JSON内容验证:")
                    print(f"  - 包含评分项: {len(data.get('scoring_contents', {}))}")
                    print(f"  - 文档统计: {'✅' if 'document_statistics' in data else '❌'}")
                    print(f"  - 章节结构: {'✅' if 'section_structure' in data else '❌'}")
                    
                    scoring_contents = data.get('scoring_contents', {})
                    for item_type, item_data in scoring_contents.items():
                        status = "✅" if item_data.get("extraction_success") else "❌"
                        content_length = len(item_data.get("content", ""))
                        print(f"    {status} {item_data.get('name', item_type)}: {content_length} 字符")
                        
                except Exception as e:
                    print(f"⚠️ JSON文件验证失败: {e}")
        else:
            print("⚠️ 输出目录不存在，分项内容可能未保存")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n" + "=" * 80)
    print("🏁 测试完成")
    print("=" * 80)

if __name__ == "__main__":
    main()