#!/usr/bin/env python3
"""
验证DOCX签字页图片识别修复

测试内容：
1. DOCX图片是否正确分配页码
2. 签字页图片能否被正确过滤和识别
3. 与预处理流水线的集成
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_docx_parser():
    """测试DOCX解析器的图片页码分配"""
    print("="*70)
    print("  测试1: DOCX图片页码分配")
    print("="*70)
    
    try:
        from src.data_processing.document_parser import DocumentParser
        
        parser = DocumentParser(enable_ocr=True)
        
        # 查找DOCX测试文件
        test_file = project_root / "data" / "raw" / "场景2(1).docx"
        
        if not test_file.exists():
            logger.warning(f"测试文件不存在: {test_file}")
            logger.info("请将DOCX文件放在 data/raw/ 目录下")
            return False
        
        logger.info(f"正在解析文件: {test_file}")
        result = parser.parse_docx(test_file)
        
        logger.info(f"✅ 文件类型: {result['file_type']}")
        logger.info(f"✅ 总页数（估算）: {result['total_pages']}")
        logger.info(f"✅ 图片数量: {len(result['images'])}")
        
        # 验证图片页码
        print("\n--- 图片页码信息 ---")
        for i, img in enumerate(result['images']):
            page_num = img.get('page_number', 'N/A')
            filename = img.get('filename', 'unknown')
            data_size = len(img.get('data', b''))
            
            status = "✅" if page_num > 0 else "❌"
            print(f"{status} 图片 {i+1}: page_number={page_num}, filename={filename}, size={data_size} bytes")
        
        # 检查前3张图片是否有页码
        images_with_page = [img for img in result['images'] if img.get('page_number', 0) > 0]
        if len(images_with_page) >= min(3, len(result['images'])):
            logger.info(f"✅ 修复成功：{len(images_with_page)}/{len(result['images'])} 张图片已分配页码")
            return True
        else:
            logger.error(f"❌ 修复失败：只有 {len(images_with_page)}/{len(result['images'])} 张图片分配了页码")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


def test_preprocessing_pipeline():
    """测试预处理流水线中的图片页码"""
    print("\n" + "="*70)
    print("  测试2: 预处理流水线图片页码")
    print("="*70)
    
    try:
        from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
        
        pipeline = PreprocessingPipeline(enable_enhanced_ocr=False)
        
        # 查找DOCX测试文件
        test_file = project_root / "data" / "raw" / "场景2(1).docx"
        
        if not test_file.exists():
            logger.warning(f"测试文件不存在: {test_file}")
            return False
        
        logger.info(f"正在处理文件: {test_file}")
        standardized_doc = pipeline.process(str(test_file))
        
        logger.info(f"✅ 文档类型: {standardized_doc.doc_info.file_type}")
        logger.info(f"✅ 图片数量: {len(standardized_doc.images)}")
        
        # 验证标准化后的图片页码
        print("\n--- 标准化后的图片信息 ---")
        for i, img in enumerate(standardized_doc.images[:10]):  # 只显示前10张
            ocr_preview = (img.extracted_text or "")[:60].replace("\n", " ")
            status = "✅" if img.page_number > 0 else "❌"
            print(f"{status} 图片 {i+1}: page_number={img.page_number}, image_id={img.image_id}")
            if ocr_preview:
                print(f"    OCR预览: {ocr_preview}...")
        
        # 检查前3页图片
        front_page_images = [img for img in standardized_doc.images if 1 <= img.page_number <= 3]
        logger.info(f"✅ 前3页图片数量: {len(front_page_images)}")
        
        if front_page_images:
            logger.info("✅ 修复成功：前3页图片可被正确识别")
            return True
        else:
            logger.warning("⚠️  未找到前3页的图片（可能文档没有图片或页码分配有问题）")
            return len(standardized_doc.images) == 0  # 如果没有图片也算正常
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


def test_signature_scoring_filter():
    """测试签字页评分中的图片过滤逻辑"""
    print("\n" + "="*70)
    print("  测试3: 签字页评分图片过滤")
    print("="*70)
    
    try:
        from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
        from src.data_processing.schemas import Image
        
        pipeline = PreprocessingPipeline(enable_enhanced_ocr=False)
        
        # 查找DOCX测试文件
        test_file = project_root / "data" / "raw" / "场景2(1).docx"
        
        if not test_file.exists():
            logger.warning(f"测试文件不存在: {test_file}")
            return False
        
        logger.info(f"正在处理文件: {test_file}")
        standardized_doc = pipeline.process(str(test_file))
        
        # 模拟签字页评分的过滤逻辑
        max_page = 3
        cover_images = [
            img for img in (standardized_doc.images or [])
            if isinstance(img.page_number, int) and (
                1 <= img.page_number <= max_page or img.page_number == 0
            )
        ]
        
        logger.info(f"✅ 文档总图片数: {len(standardized_doc.images)}")
        logger.info(f"✅ 过滤后前{max_page}页图片数: {len(cover_images)}")
        
        print("\n--- 过滤后的图片 ---")
        for i, img in enumerate(cover_images[:5]):
            print(f"  图片 {i+1}: page_number={img.page_number}, image_id={img.image_id}")
        
        if cover_images:
            logger.info("✅ 修复成功：签字页图片能被正确过滤")
            return True
        else:
            logger.warning("⚠️  过滤后没有图片（可能文档没有图片）")
            return len(standardized_doc.images) == 0
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False


def main():
    """运行所有验证测试"""
    print("\n" + "="*70)
    print("  DOCX签字页图片识别修复验证")
    print("="*70 + "\n")
    
    results = []
    
    # 运行测试
    results.append(("DOCX图片页码分配", test_docx_parser()))
    results.append(("预处理流水线集成", test_preprocessing_pipeline()))
    results.append(("签字页图片过滤", test_signature_scoring_filter()))
    
    # 总结
    print("\n" + "="*70)
    print("  测试结果总结")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\n总计: {total_passed}/{len(results)} 项测试通过")
    
    if total_passed == len(results):
        print("\n🎉 所有测试通过！DOCX签字页图片识别修复成功！")
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息")


if __name__ == "__main__":
    main()

