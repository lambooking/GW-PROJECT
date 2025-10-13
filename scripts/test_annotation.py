#!/usr/bin/env python3
"""
测试文档批注功能
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.annotation import AnnotationManager, Annotation, AnnotationSeverity, AnnotationType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_annotation_schemas():
    """测试批注数据结构"""
    logger.info("=" * 60)
    logger.info("测试批注数据结构")
    logger.info("=" * 60)
    
    # 创建测试批注
    annotation = Annotation(
        location="第2页 第3段",
        page_number=2,
        annotation_type=AnnotationType.COMMENT,
        severity=AnnotationSeverity.WARNING,
        score_item="内容完整性",
        content="缺少详细的操作步骤说明",
        suggestion="建议补充具体的操作流程和注意事项",
        score_lost=3.0,
        max_score=30.0,
        text_snippet="管道处及时掌握险情动态..."
    )
    
    logger.info(f"批注位置: {annotation.location}")
    logger.info(f"严重程度: {annotation.severity}")
    logger.info(f"颜色代码: {annotation.get_color_code()}")
    logger.info(f"格式化内容:\n{annotation.get_formatted_content()}")
    
    logger.info("✅ 批注数据结构测试通过")


def test_docx_annotation():
    """测试DOCX批注功能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试DOCX文档批注")
    logger.info("=" * 60)
    
    # 查找测试文件
    test_files = list(Path("data/raw").glob("*.docx"))
    
    if not test_files:
        logger.warning("未找到DOCX测试文件，跳过测试")
        return
    
    test_file = test_files[0]
    logger.info(f"测试文件: {test_file}")
    
    # 创建测试批注
    annotations = [
        Annotation(
            location="文档开头",
            page_number=1,
            annotation_type=AnnotationType.COMMENT,
            severity=AnnotationSeverity.WARNING,
            score_item="结构完整性",
            content="缺少必需的章节：记录文件",
            suggestion="建议添加'记录文件'章节，列出相关记录表格",
            score_lost=5.0,
            max_score=20.0,
            section_name="目录"
        ),
        Annotation(
            location="第1页",
            page_number=1,
            annotation_type=AnnotationType.HIGHLIGHT,
            severity=AnnotationSeverity.INFO,
            score_item="语法规范性",
            content="表述较为清晰，建议进一步规范化",
            score_lost=1.0,
            max_score=10.0
        )
    ]
    
    # 生成批注文档
    manager = AnnotationManager()
    output_file = Path("output/test_annotated.docx")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 模拟评分结果
        scoring_result = {
            "annotations": [ann.dict() for ann in annotations],
            "scoring_details": {}
        }
        
        annotated_file = manager.annotate_document(
            test_file,
            scoring_result,
            output_file
        )
        
        logger.info(f"✅ DOCX批注测试成功: {annotated_file}")
    except Exception as e:
        logger.error(f"❌ DOCX批注测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_pdf_annotation():
    """测试PDF批注功能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试PDF文档批注")
    logger.info("=" * 60)
    
    # 查找测试文件
    test_files = list(Path("data/raw").glob("*.pdf"))
    
    if not test_files:
        logger.warning("未找到PDF测试文件，跳过测试")
        return
    
    test_file = test_files[0]
    logger.info(f"测试文件: {test_file}")
    
    # 创建测试批注
    annotations = [
        Annotation(
            location="第1页 顶部",
            page_number=1,
            annotation_type=AnnotationType.COMMENT,
            severity=AnnotationSeverity.CRITICAL,
            score_item="技术准确性",
            content="技术参数表中缺少管径规格信息",
            suggestion="建议补充完整的管径、材质、壁厚等技术参数",
            score_lost=8.0,
            max_score=25.0,
            coordinates={"x0": 100, "y0": 100, "x1": 400, "y1": 150}
        ),
        Annotation(
            location="第2页",
            page_number=2,
            annotation_type=AnnotationType.HIGHLIGHT,
            severity=AnnotationSeverity.WARNING,
            score_item="安全合规性",
            content="安全措施描述不够详细",
            suggestion="建议增加具体的安全防护措施和应急预案",
            score_lost=3.5,
            max_score=15.0,
            text_snippet="安全要求 风险控制"
        )
    ]
    
    # 生成批注文档
    manager = AnnotationManager()
    output_file = Path("output/test_annotated.pdf")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 模拟评分结果
        scoring_result = {
            "annotations": [ann.dict() for ann in annotations],
            "scoring_details": {}
        }
        
        annotated_file = manager.annotate_document(
            test_file,
            scoring_result,
            output_file
        )
        
        logger.info(f"✅ PDF批注测试成功: {annotated_file}")
    except Exception as e:
        logger.error(f"❌ PDF批注测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_annotation_report():
    """测试批注报告生成"""
    logger.info("\n" + "=" * 60)
    logger.info("测试批注报告生成")
    logger.info("=" * 60)
    
    # 创建测试批注
    annotations = [
        Annotation(
            location="第1页",
            page_number=1,
            annotation_type=AnnotationType.COMMENT,
            severity=AnnotationSeverity.CRITICAL,
            score_item="结构完整性",
            content="缺少必需章节",
            suggestion="补充缺失章节",
            score_lost=5.0,
            max_score=20.0
        ),
        Annotation(
            location="第2页",
            page_number=2,
            annotation_type=AnnotationType.COMMENT,
            severity=AnnotationSeverity.WARNING,
            score_item="内容完整性",
            content="内容不够详细",
            suggestion="完善内容描述",
            score_lost=3.0,
            max_score=30.0
        ),
        Annotation(
            location="第3页",
            page_number=3,
            annotation_type=AnnotationType.COMMENT,
            severity=AnnotationSeverity.INFO,
            score_item="语法规范性",
            content="个别表述可优化",
            suggestion="规范语言表述",
            score_lost=1.0,
            max_score=10.0
        )
    ]
    
    # 生成报告
    manager = AnnotationManager()
    report_file = Path("output/test_annotation_report.txt")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        manager.generate_annotation_report(annotations, report_file)
        logger.info(f"✅ 批注报告生成成功: {report_file}")
        
        # 读取并显示报告内容
        content = report_file.read_text(encoding='utf-8')
        print("\n" + "=" * 60)
        print("批注报告内容预览:")
        print("=" * 60)
        print(content[:500] + "...")
        
    except Exception as e:
        logger.error(f"❌ 批注报告生成失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试函数"""
    logger.info("🧪 开始测试文档批注功能")
    
    try:
        # 测试批注数据结构
        test_annotation_schemas()
        
        # 测试DOCX批注
        test_docx_annotation()
        
        # 测试PDF批注
        test_pdf_annotation()
        
        # 测试批注报告
        test_annotation_report()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 所有测试完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


