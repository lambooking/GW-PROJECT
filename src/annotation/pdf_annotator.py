"""
PDF文档批注器实现
"""

import logging
import shutil
from pathlib import Path
from typing import List, Union, Optional

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from .base import BaseAnnotator
from .schemas import Annotation, AnnotationSeverity

logger = logging.getLogger(__name__)


class PdfAnnotator(BaseAnnotator):
    """PDF文档批注器"""
    
    def __init__(self):
        """初始化PDF批注器"""
        super().__init__()
        self.supported_extensions = ['.pdf']
        
        if not PYMUPDF_AVAILABLE:
            raise ImportError("需要安装 PyMuPDF: pip install PyMuPDF")
    
    def annotate(
        self,
        input_file: Union[str, Path],
        annotations: List[Annotation],
        output_file: Union[str, Path]
    ) -> Path:
        """在PDF文档上添加批注"""
        input_file = self._validate_file(input_file)
        output_file = Path(output_file)
        
        logger.info(f"开始为PDF文档添加批注: {input_file}")
        self._log_annotation_stats(annotations)
        
        # 打开PDF文档
        doc = fitz.open(input_file)
        
        # 按页码分组批注
        page_annotations = self._sort_annotations_by_page(annotations)
        
        # 逐页添加批注
        added_count = 0
        for page_num, page_anns in page_annotations.items():
            try:
                # 页码从1开始，fitz从0开始
                page_idx = page_num - 1
                
                if page_idx < 0 or page_idx >= len(doc):
                    logger.warning(f"页码超出范围: {page_num}")
                    continue
                
                page = doc[page_idx]
                
                for ann in page_anns:
                    success = self._add_annotation_to_page(page, ann)
                    if success:
                        added_count += 1
            except Exception as e:
                logger.error(f"处理第 {page_num} 页时出错: {e}")
                continue
        
        # 添加批注汇总页
        self._add_summary_page(doc, annotations)
        
        # 保存文档
        doc.save(output_file)
        doc.close()
        
        logger.info(f"成功添加 {added_count}/{len(annotations)} 条批注，已保存到: {output_file}")
        return output_file
    
    def _add_annotation_to_page(self, page: fitz.Page, annotation: Annotation) -> bool:
        """在PDF页面上添加批注"""
        try:
            # 策略1: 如果有坐标信息，使用坐标定位
            if annotation.coordinates:
                return self._add_annotation_with_coordinates(page, annotation)
            
            # 策略2: 如果有文本片段，搜索文本定位
            if annotation.text_snippet:
                return self._add_annotation_with_text_search(page, annotation)
            
            # 策略3: 在页面顶部添加通用批注
            return self._add_annotation_at_top(page, annotation)
            
        except Exception as e:
            logger.warning(f"添加批注失败: {e}")
            return False
    
    def _add_annotation_with_coordinates(self, page: fitz.Page, annotation: Annotation) -> bool:
        """使用坐标添加批注"""
        try:
            coords = annotation.coordinates
            rect = fitz.Rect(
                coords.get('x0', 0),
                coords.get('y0', 0),
                coords.get('x1', 100),
                coords.get('y1', 50)
            )
            
            # 高亮区域
            self._add_highlight(page, rect, annotation.severity)
            
            # 在区域右侧添加文本批注
            comment_point = fitz.Point(rect.x1 + 5, rect.y0)
            self._add_text_annotation(page, comment_point, annotation)
            
            return True
        except Exception as e:
            logger.debug(f"坐标批注添加失败: {e}")
            return False
    
    def _add_annotation_with_text_search(self, page: fitz.Page, annotation: Annotation) -> bool:
        """通过搜索文本添加批注"""
        try:
            # 搜索文本
            search_text = annotation.text_snippet.strip()[:50]  # 取前50字符
            text_instances = page.search_for(search_text)
            
            if not text_instances:
                logger.debug(f"未找到文本: {search_text[:20]}...")
                return self._add_annotation_at_top(page, annotation)
            
            # 使用第一个匹配
            rect = text_instances[0]
            
            # 高亮文本
            self._add_highlight(page, rect, annotation.severity)
            
            # 添加批注
            comment_point = fitz.Point(rect.x1 + 5, rect.y0)
            self._add_text_annotation(page, comment_point, annotation)
            
            return True
        except Exception as e:
            logger.debug(f"文本搜索批注失败: {e}")
            return False
    
    def _add_annotation_at_top(self, page: fitz.Page, annotation: Annotation) -> bool:
        """在页面顶部添加批注"""
        try:
            # 在页面顶部添加批注框
            page_rect = page.rect
            
            # 批注框位置（页面顶部右侧）
            annot_width = 150
            annot_height = 80
            rect = fitz.Rect(
                page_rect.width - annot_width - 10,
                10,
                page_rect.width - 10,
                10 + annot_height
            )
            
            # 添加文本框批注
            self._add_freetext_annotation(page, rect, annotation)
            
            return True
        except Exception as e:
            logger.debug(f"顶部批注添加失败: {e}")
            return False
    
    def _add_highlight(self, page: fitz.Page, rect: fitz.Rect, severity: AnnotationSeverity) -> None:
        """添加高亮"""
        try:
            # 根据严重程度选择颜色
            color = self._get_color_for_severity(severity)
            
            # 添加高亮批注
            highlight = page.add_highlight_annot(rect)
            highlight.set_colors(stroke=color)
            highlight.update()
        except Exception as e:
            logger.debug(f"添加高亮失败: {e}")
    
    def _add_text_annotation(self, page: fitz.Page, point: fitz.Point, annotation: Annotation) -> None:
        """添加文本批注（图钉样式）"""
        try:
            # 创建文本批注
            text_annot = page.add_text_annot(
                point,
                annotation.get_formatted_content(),
                icon="Comment"
            )
            
            # 设置颜色
            color = self._get_color_for_severity(annotation.severity)
            text_annot.set_colors(stroke=color)
            
            # 设置批注信息
            info = text_annot.info
            info["title"] = annotation.author
            info["subject"] = annotation.score_item
            text_annot.set_info(info)
            
            text_annot.update()
        except Exception as e:
            logger.debug(f"添加文本批注失败: {e}")
    
    def _add_freetext_annotation(self, page: fitz.Page, rect: fitz.Rect, annotation: Annotation) -> None:
        """添加自由文本批注（文本框）"""
        try:
            # 创建文本框
            # 格式化批注内容（简短版）
            short_content = f"【{annotation.score_item}】\n"
            short_content += f"扣分: {annotation.score_lost:.1f}分\n"
            short_content += f"{annotation.content[:60]}..."
            
            freetext = page.add_freetext_annot(
                rect,
                short_content,
                fontsize=8,
                fontname="china-s",  # 支持中文
                text_color=self._get_color_for_severity(annotation.severity),
                fill_color=(1, 1, 0.9)  # 浅黄色背景
            )
            
            # 设置边框颜色
            freetext.set_border(width=1, dashes=[2])
            freetext.set_colors(stroke=self._get_color_for_severity(annotation.severity))
            
            freetext.update()
        except Exception as e:
            logger.debug(f"添加文本框批注失败: {e}")
    
    def _get_color_for_severity(self, severity: AnnotationSeverity) -> tuple:
        """获取严重程度对应的颜色（RGB，0-1范围）"""
        if severity == AnnotationSeverity.CRITICAL:
            return (1.0, 0.0, 0.0)  # 红色
        elif severity == AnnotationSeverity.WARNING:
            return (1.0, 0.65, 0.0)  # 橙色
        else:
            return (0.0, 0.5, 1.0)  # 蓝色
    
    def _add_summary_page(self, doc: fitz.Document, annotations: List[Annotation]) -> None:
        """在文档末尾添加批注汇总页"""
        if not annotations:
            return
        
        try:
            # 添加新页
            page = doc.new_page()
            
            # 页面尺寸
            page_width = page.rect.width
            page_height = page.rect.height
            
            # 标题
            title_rect = fitz.Rect(50, 50, page_width - 50, 80)
            title_text = "评分批注汇总"
            page.insert_textbox(
                title_rect,
                title_text,
                fontsize=16,
                fontname="china-s",
                color=(0, 0, 0),
                align=fitz.TEXT_ALIGN_CENTER
            )
            
            # 统计信息
            critical = len([a for a in annotations if a.severity == AnnotationSeverity.CRITICAL])
            warning = len([a for a in annotations if a.severity == AnnotationSeverity.WARNING])
            info = len([a for a in annotations if a.severity == AnnotationSeverity.INFO])
            
            stats_y = 100
            stats_rect = fitz.Rect(50, stats_y, page_width - 50, stats_y + 80)
            stats_text = f"总批注数: {len(annotations)} 条\n"
            stats_text += f"严重问题: {critical} 条\n"
            stats_text += f"一般问题: {warning} 条\n"
            stats_text += f"建议改进: {info} 条"
            
            page.insert_textbox(
                stats_rect,
                stats_text,
                fontsize=12,
                fontname="china-s",
                color=(0, 0, 0)
            )
            
            # 详细批注列表
            list_y = 200
            list_text = "\n详细批注列表：\n\n"
            
            for idx, ann in enumerate(annotations[:20], 1):  # 限制前20条
                severity_icon = {
                    AnnotationSeverity.CRITICAL: "🔴",
                    AnnotationSeverity.WARNING: "🟡",
                    AnnotationSeverity.INFO: "🔵"
                }.get(ann.severity, "⚪")
                
                list_text += f"{idx}. {severity_icon} [{ann.location}] {ann.score_item}\n"
                list_text += f"   扣分: {ann.score_lost:.1f}分 - {ann.content[:50]}...\n\n"
            
            if len(annotations) > 20:
                list_text += f"\n... 还有 {len(annotations) - 20} 条批注，请查看正文中的详细标注。"
            
            list_rect = fitz.Rect(50, list_y, page_width - 50, page_height - 50)
            page.insert_textbox(
                list_rect,
                list_text,
                fontsize=9,
                fontname="china-s",
                color=(0, 0, 0)
            )
            
            logger.info("已添加批注汇总页")
        except Exception as e:
            logger.warning(f"添加汇总页失败: {e}")

