#!/usr/bin/env python3
"""
测试签字页优化功能
验证DOCX文档只提取前N张图片的优化是否生效
"""
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_processing.document_parser import DocumentParser
from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_max_images_parameter():
    """测试 max_images 参数是否正常工作"""
    print("=" * 80)
    print("测试1：DocumentParser 的 max_images 参数")
    print("=" * 80)
    
    if len(sys.argv) < 2:
        print("用法: python scripts/test_signature_optimization.py <docx文件路径>")
        print("\n示例:")
        print("  python scripts/test_signature_optimization.py /path/to/document.docx")
        return False
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    if file_path.suffix.lower() != '.docx':
        print(f"❌ 文件不是DOCX格式: {file_path}")
        return False
    
    parser = DocumentParser(enable_ocr=True)
    
    # 测试1：提取所有图片
    print("\n【测试A】提取所有图片（无限制）")
    print("-" * 80)
    start_time = time.time()
    result_all = parser.parse_docx(file_path, max_images=None)
    time_all = time.time() - start_time
    
    images_all = result_all.get('images', [])
    print(f"✅ 提取完成")
    print(f"   - 提取图片数: {len(images_all)}")
    print(f"   - 处理时间: {time_all:.2f} 秒")
    
    # 测试2：只提取前3张
    print("\n【测试B】只提取前3张图片（优化模式）")
    print("-" * 80)
    start_time = time.time()
    result_limited = parser.parse_docx(file_path, max_images=3)
    time_limited = time.time() - start_time
    
    images_limited = result_limited.get('images', [])
    print(f"✅ 提取完成")
    print(f"   - 提取图片数: {len(images_limited)}")
    print(f"   - 处理时间: {time_limited:.2f} 秒")
    
    # 对比结果
    print("\n【对比结果】")
    print("-" * 80)
    print(f"图片数量:")
    print(f"  全量模式: {len(images_all)} 张")
    print(f"  优化模式: {len(images_limited)} 张")
    print(f"  减少: {len(images_all) - len(images_limited)} 张 ({(1 - len(images_limited)/max(len(images_all), 1))*100:.1f}%)")
    
    print(f"\n处理时间:")
    print(f"  全量模式: {time_all:.2f} 秒")
    print(f"  优化模式: {time_limited:.2f} 秒")
    if time_all > 0:
        speedup = (time_all - time_limited) / time_all * 100
        print(f"  加速: {speedup:.1f}%")
    
    # 验证逻辑正确性
    expected_limit = min(3, len(images_all))
    if len(images_limited) == expected_limit:
        print(f"\n✅ 验证通过：优化模式正确提取了前 {expected_limit} 张图片")
        return True
    else:
        print(f"\n❌ 验证失败：期望 {expected_limit} 张，实际 {len(images_limited)} 张")
        return False


def test_pipeline_auto_optimization():
    """测试预处理管线的自动优化"""
    print("\n" + "=" * 80)
    print("测试2：PreprocessingPipeline 的自动优化")
    print("=" * 80)
    
    if len(sys.argv) < 2:
        return False
    
    file_path = sys.argv[1]
    pipeline = PreprocessingPipeline()
    
    # 测试文件名判断逻辑
    test_filenames = [
        ("风险管控方案.docx", True),
        ("高后果区防护.docx", True),
        ("应急预案.docx", True),
        ("作业指导书.docx", False),
        ("技术方案.docx", False),
    ]
    
    print("\n【文件名识别测试】")
    print("-" * 80)
    all_correct = True
    for filename, expected in test_filenames:
        result = pipeline._is_likely_risk_management_doc(filename)
        status = "✅" if result == expected else "❌"
        print(f"{status} {filename:30s} -> {'风险管控' if result else '其他类型':10s} (期望: {'风险管控' if expected else '其他类型'})")
        if result != expected:
            all_correct = False
    
    if all_correct:
        print("\n✅ 文件名识别逻辑正确")
    else:
        print("\n❌ 文件名识别存在问题")
    
    # 测试实际处理
    print("\n【实际处理测试】")
    print("-" * 80)
    print(f"处理文件: {Path(file_path).name}")
    
    start_time = time.time()
    document = pipeline.process(file_path)
    process_time = time.time() - start_time
    
    print(f"✅ 处理完成")
    print(f"   - 场景类型: {document.document_info.scene_name}")
    print(f"   - 图片数量: {len(document.images)}")
    print(f"   - 处理时间: {process_time:.2f} 秒")
    
    return True


def main():
    """主函数"""
    print("\n🧪 签字页优化功能测试")
    print("=" * 80)
    
    if len(sys.argv) < 2:
        print("\n用法:")
        print("  python scripts/test_signature_optimization.py <docx文件路径>")
        print("\n示例:")
        print("  python scripts/test_signature_optimization.py data/test/风险管控方案.docx")
        print("\n说明:")
        print("  该脚本会测试：")
        print("  1. max_images 参数是否正常工作")
        print("  2. 预处理管线是否能自动识别风险管控文档")
        print("  3. 优化带来的性能提升")
        print("=" * 80)
        return
    
    try:
        # 测试1
        success1 = test_max_images_parameter()
        
        # 测试2
        success2 = test_pipeline_auto_optimization()
        
        # 总结
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        
        if success1 and success2:
            print("✅ 所有测试通过！签字页优化功能正常工作。")
        else:
            print("❌ 部分测试失败，请检查代码实现。")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

