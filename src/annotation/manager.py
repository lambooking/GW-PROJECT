"""
批注管理器 - 统一管理不同格式的文档批注
"""

import logging
from pathlib import Path
from typing import List, Union, Optional, Dict, Any

from .base import BaseAnnotator
from .docx_annotator import DocxAnnotator
from .pdf_annotator import PdfAnnotator
from .schemas import Annotation, AnnotationCollection, AnnotationSeverity, AnnotationType

logger = logging.getLogger(__name__)


class AnnotationManager:
    """批注管理器"""
    
    def __init__(self):
        """初始化批注管理器"""
        self.annotators = {
            '.docx': DocxAnnotator(),
            '.pdf': PdfAnnotator()
        }
    
    def annotate_document(
        self,
        original_file: Union[str, Path],
        scoring_result: Dict[str, Any],
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        为文档添加批注
        
        Args:
            original_file: 原始文档路径
            scoring_result: 评分结果（包含批注信息）
            output_path: 输出路径（可选，默认在原文件同目录生成）
            
        Returns:
            批注后的文档路径
        """
        original_file = Path(original_file)
        
        if not original_file.exists():
            raise FileNotFoundError(f"文件不存在: {original_file}")
        
        # 确定输出路径
        if output_path is None:
            output_path = self._generate_output_path(original_file)
        else:
            output_path = Path(output_path)
        
        # 生成批注列表
        annotations = self._generate_annotations_from_scoring(scoring_result)
        
        if not annotations:
            logger.warning("没有生成任何批注")
            return original_file
        
        # 选择合适的批注器
        annotator = self._get_annotator(original_file)
        
        if annotator is None:
            raise ValueError(f"不支持的文件格式: {original_file.suffix}")
        
        # 执行批注
        logger.info(f"使用 {annotator.__class__.__name__} 处理文档")
        annotated_file = annotator.annotate(original_file, annotations, output_path)
        
        logger.info(f"批注完成: {annotated_file}")
        return annotated_file
    
    def _generate_output_path(self, original_file: Path) -> Path:
        """生成输出文件路径"""
        stem = original_file.stem
        suffix = original_file.suffix
        parent = original_file.parent
        
        # 生成带批注标记的文件名
        output_name = f"{stem}_批注版{suffix}"
        return parent / output_name
    
    def _get_annotator(self, file_path: Path) -> Optional[BaseAnnotator]:
        """获取合适的批注器"""
        ext = file_path.suffix.lower()
        return self.annotators.get(ext)
    
    def _generate_annotations_from_scoring(
        self,
        scoring_result: Dict[str, Any]
    ) -> List[Annotation]:
        """
        从评分结果生成批注列表
        
        Args:
            scoring_result: 评分结果字典
            
        Returns:
            批注列表
        """
        annotations = []
        
        # 检查是否已经有批注列表
        if 'annotations' in scoring_result:
            return scoring_result['annotations']
        
        # 从评分详情生成批注
        scoring_details = scoring_result.get('scoring_details', {})
        document_info = scoring_result.get('document_info', {})
        
        for criterion_key, criterion_result in scoring_details.items():
            # 提取评分信息
            score = criterion_result.get('score', 0)
            max_score = criterion_result.get('max_score', 0)
            score_lost = max_score - score
            
            # 只为扣分项生成批注
            if score_lost <= 0:
                continue
            
            # 确定严重程度
            severity = self._determine_severity(score_lost, max_score)
            
            # 生成批注
            annotation = Annotation(
                location=self._extract_location(criterion_result),
                page_number=self._extract_page_number(criterion_result),
                annotation_type=AnnotationType.COMMENT,
                severity=severity,
                score_item=criterion_result.get('name', criterion_key),
                content=criterion_result.get('reasoning', '需要改进'),
                suggestion=self._extract_suggestion(criterion_result),
                score_lost=score_lost,
                max_score=max_score,
                text_snippet=self._extract_text_snippet(criterion_result),
                section_name=self._extract_section_name(criterion_result),
                coordinates=criterion_result.get('coordinates')
            )
            
            annotations.append(annotation)
        
        logger.info(f"从评分结果生成了 {len(annotations)} 条批注")
        return annotations
    
    def _determine_severity(self, score_lost: float, max_score: float) -> AnnotationSeverity:
        """确定严重程度"""
        if score_lost >= 5:
            return AnnotationSeverity.CRITICAL
        elif score_lost >= 2:
            return AnnotationSeverity.WARNING
        else:
            return AnnotationSeverity.INFO
    
    def _extract_location(self, criterion_result: Dict) -> str:
        """提取位置信息"""
        # 尝试多种方式提取位置
        location = criterion_result.get('location')
        if location:
            return location
        
        # 从上下文中提取
        context = criterion_result.get('context_used', '')
        if context:
            # 简单的位置描述
            return f"相关内容区域"
        
        return "文档中"
    
    def _extract_page_number(self, criterion_result: Dict) -> int:
        """提取页码"""
        page = criterion_result.get('page_number')
        if page:
            return page
        
        # 默认返回第1页
        return 1
    
    def _extract_suggestion(self, criterion_result: Dict) -> Optional[str]:
        """提取修改建议"""
        # 尝试多种字段
        for key in ['suggestion', 'suggestions', 'improvement']:
            value = criterion_result.get(key)
            if value:
                if isinstance(value, list):
                    return "; ".join(value)
                return str(value)
        
        return None
    
    def _extract_text_snippet(self, criterion_result: Dict) -> Optional[str]:
        """提取文本片段用于定位"""
        # 从上下文中提取
        context = criterion_result.get('context_used', '')
        if context:
            # 取前200字符作为片段
            return context[:200]
        
        return None
    
    def _extract_section_name(self, criterion_result: Dict) -> Optional[str]:
        """提取章节名称"""
        return criterion_result.get('section_name')
    
    def generate_annotation_report(
        self,
        annotations: List[Annotation],
        output_path: Union[str, Path]
    ) -> Path:
        """
        生成批注报告（纯文本格式）
        
        Args:
            annotations: 批注列表
            output_path: 输出路径
            
        Returns:
            报告文件路径
        """
        output_path = Path(output_path)
        
        # 按严重程度分组
        critical = [a for a in annotations if a.severity == AnnotationSeverity.CRITICAL]
        warning = [a for a in annotations if a.severity == AnnotationSeverity.WARNING]
        info = [a for a in annotations if a.severity == AnnotationSeverity.INFO]
        
        # 生成报告内容
        lines = [
            "=" * 60,
            "批注报告",
            "=" * 60,
            "",
            f"生成时间: {annotations[0].created_at if annotations else ''}",
            f"总批注数: {len(annotations)} 条",
            f"  - 严重问题: {len(critical)} 条",
            f"  - 一般问题: {len(warning)} 条",
            f"  - 建议改进: {len(info)} 条",
            "",
            "=" * 60,
            ""
        ]
        
        # 按严重程度输出
        for severity_name, severity_list in [
            ("严重问题", critical),
            ("一般问题", warning),
            ("建议改进", info)
        ]:
            if severity_list:
                lines.append(f"\n{severity_name} ({len(severity_list)} 条):")
                lines.append("-" * 60)
                
                for idx, ann in enumerate(severity_list, 1):
                    lines.append(f"\n{idx}. [{ann.location}] {ann.score_item}")
                    lines.append(f"   页码: 第{ann.page_number}页")
                    lines.append(f"   扣分: {ann.score_lost:.1f}/{ann.max_score:.1f}分")
                    lines.append(f"   问题: {ann.content}")
                    if ann.suggestion:
                        lines.append(f"   建议: {ann.suggestion}")
                    lines.append("")
        
        # 写入文件
        report_text = "\n".join(lines)
        output_path.write_text(report_text, encoding='utf-8')
        
        logger.info(f"批注报告已生成: {output_path}")
        return output_path

