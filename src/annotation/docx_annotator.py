"""
DOCX文档批注器实现
"""

import logging
import shutil
from pathlib import Path
from typing import List, Union, Optional
from datetime import datetime

try:
    from docx import Document
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import qn
    from docx.shared import RGBColor, Pt
    from docx.enum.text import WD_COLOR_INDEX
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False

from .base import BaseAnnotator
from .schemas import Annotation, AnnotationSeverity

logger = logging.getLogger(__name__)


class DocxAnnotator(BaseAnnotator):
    """DOCX文档批注器"""
    
    def __init__(self):
        """初始化DOCX批注器"""
        super().__init__()
        self.supported_extensions = ['.docx']
        
        if not PYTHON_DOCX_AVAILABLE:
            raise ImportError("需要安装 python-docx: pip install python-docx")
        
        # 批注ID计数器
        self._comment_id = 0
    
    def annotate(
        self,
        input_file: Union[str, Path],
        annotations: List[Annotation],
        output_file: Union[str, Path]
    ) -> Path:
        """在DOCX文档上添加批注"""
        input_file = self._validate_file(input_file)
        output_file = Path(output_file)
        
        logger.info(f"开始为DOCX文档添加批注: {input_file}")
        self._log_annotation_stats(annotations)
        
        # 复制原文件
        shutil.copy2(input_file, output_file)
        
        # 打开文档
        doc = Document(output_file)
        
        # 初始化批注部分
        self._init_comments_part(doc)
        
        # 按页码/位置分组批注
        annotations_by_location = self._group_annotations(annotations)
        
        # 添加批注
        added_count = 0
        for ann in annotations:
            try:
                success = self._add_annotation_to_document(doc, ann)
                if success:
                    added_count += 1
            except Exception as e:
                logger.warning(f"添加批注失败: {e}")
                continue
        
        # 保存文档
        doc.save(output_file)
        
        logger.info(f"成功添加 {added_count}/{len(annotations)} 条批注，已保存到: {output_file}")
        return output_file
    
    def _init_comments_part(self, doc: Document) -> None:
        """初始化文档的批注部分"""
        # 检查是否已有批注部分
        try:
            comments_part = doc.part.part_related_by(
                'http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments'
            )
        except KeyError:
            # 如果没有批注部分，创建一个
            # 注意：python-docx不直接支持批注，这里使用高亮作为替代方案
            pass
    
    def _group_annotations(self, annotations: List[Annotation]) -> dict:
        """按位置分组批注"""
        grouped = {}
        for ann in annotations:
            key = (ann.page_number, ann.section_name or ann.location)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(ann)
        return grouped
    
    def _add_annotation_to_document(self, doc: Document, annotation: Annotation) -> bool:
        """
        将批注添加到文档
        
        由于python-docx对批注的支持有限，这里采用以下策略：
        1. 查找匹配的段落
        2. 在段落后插入带颜色的批注文本框
        3. 高亮原文（如果找到匹配文本）
        """
        
        # 查找匹配的段落
        target_para = self._find_target_paragraph(doc, annotation)
        
        if target_para is None:
            # 如果找不到精确匹配，在文档末尾添加批注汇总
            logger.debug(f"未找到匹配段落，将在末尾添加批注: {annotation.location}")
            return self._add_annotation_at_end(doc, annotation)
        
        # 在段落后添加批注段落
        return self._add_inline_annotation(doc, target_para, annotation)
    
    def _find_target_paragraph(self, doc: Document, annotation: Annotation):
        """查找目标段落"""
        
        # 策略1: 如果有文本片段，精确匹配
        if annotation.text_snippet:
            snippet = annotation.text_snippet.strip()[:100]  # 取前100字符
            for para in doc.paragraphs:
                if snippet in para.text:
                    return para
        
        # 策略2: 根据章节名称匹配
        if annotation.section_name:
            for para in doc.paragraphs:
                if annotation.section_name in para.text:
                    return para
        
        # 策略3: 根据位置描述模糊匹配
        location_keywords = annotation.location.split()
        for para in doc.paragraphs:
            if any(keyword in para.text for keyword in location_keywords):
                return para
        
        return None
    
    def _add_inline_annotation(self, doc: Document, target_para, annotation: Annotation) -> bool:
        """在段落附近添加内联批注"""
        try:
            # 获取目标段落的索引
            para_index = doc.paragraphs.index(target_para)
            
            # 高亮原段落（如果可能）
            self._highlight_paragraph(target_para, annotation.severity)
            
            # 在下一个段落位置插入批注
            # 由于python-docx不支持在特定位置插入段落，我们在段落后添加
            comment_para = doc.add_paragraph()
            
            # 设置批注样式
            comment_text = f"💬 {annotation.get_formatted_content()}"
            run = comment_para.add_run(comment_text)
            
            # 设置字体颜色和样式
            color_rgb = annotation.get_color_code()
            run.font.color.rgb = RGBColor(
                int(color_rgb[0] * 255),
                int(color_rgb[1] * 255),
                int(color_rgb[2] * 255)
            )
            run.font.size = Pt(9)
            run.font.italic = True
            
            # 设置段落背景色（通过边框和底纹）
            self._set_paragraph_background(comment_para, annotation.severity)
            
            logger.debug(f"已在段落后添加批注: {annotation.location}")
            return True
            
        except Exception as e:
            logger.warning(f"添加内联批注失败: {e}")
            return False
    
    def _highlight_paragraph(self, paragraph, severity: AnnotationSeverity) -> None:
        """高亮段落"""
        try:
            # 根据严重程度选择高亮颜色
            if severity == AnnotationSeverity.CRITICAL:
                highlight_color = WD_COLOR_INDEX.RED
            elif severity == AnnotationSeverity.WARNING:
                highlight_color = WD_COLOR_INDEX.YELLOW
            else:
                highlight_color = WD_COLOR_INDEX.TURQUOISE
            
            # 高亮段落中的所有文本
            for run in paragraph.runs:
                run.font.highlight_color = highlight_color
        except Exception as e:
            logger.debug(f"高亮段落失败: {e}")
    
    def _set_paragraph_background(self, paragraph, severity: AnnotationSeverity) -> None:
        """设置段落背景色"""
        try:
            # 获取段落的XML元素
            p = paragraph._element
            pPr = p.get_or_add_pPr()
            
            # 添加底纹
            shading_elm = OxmlElement('w:shd')
            shading_elm.set(qn('w:fill'), self._get_background_color(severity))
            pPr.append(shading_elm)
        except Exception as e:
            logger.debug(f"设置段落背景失败: {e}")
    
    def _get_background_color(self, severity: AnnotationSeverity) -> str:
        """获取背景颜色（十六进制）"""
        if severity == AnnotationSeverity.CRITICAL:
            return "FFE6E6"  # 浅红色
        elif severity == AnnotationSeverity.WARNING:
            return "FFF9E6"  # 浅黄色
        else:
            return "E6F3FF"  # 浅蓝色
    
    def _add_annotation_at_end(self, doc: Document, annotation: Annotation) -> bool:
        """在文档末尾添加批注"""
        try:
            # 添加分隔符
            doc.add_paragraph()
            separator = doc.add_paragraph("=" * 50)
            separator.runs[0].font.color.rgb = RGBColor(128, 128, 128)
            
            # 添加批注标题
            title = doc.add_paragraph(f"批注 - {annotation.location}")
            title.runs[0].bold = True
            
            # 添加批注内容
            content_para = doc.add_paragraph(annotation.get_formatted_content())
            
            # 设置颜色
            color_rgb = annotation.get_color_code()
            for run in content_para.runs:
                run.font.color.rgb = RGBColor(
                    int(color_rgb[0] * 255),
                    int(color_rgb[1] * 255),
                    int(color_rgb[2] * 255)
                )
            
            return True
        except Exception as e:
            logger.warning(f"在末尾添加批注失败: {e}")
            return False
    
    def add_annotation_summary(
        self,
        doc: Document,
        annotations: List[Annotation]
    ) -> None:
        """在文档末尾添加批注汇总"""
        
        if not annotations:
            return
        
        # 添加新页（分页符）
        doc.add_page_break()
        
        # 添加标题
        title = doc.add_paragraph("评分批注汇总")
        title.runs[0].bold = True
        title.runs[0].font.size = Pt(16)
        
        doc.add_paragraph()
        
        # 按严重程度分组
        critical = [a for a in annotations if a.severity == AnnotationSeverity.CRITICAL]
        warning = [a for a in annotations if a.severity == AnnotationSeverity.WARNING]
        info = [a for a in annotations if a.severity == AnnotationSeverity.INFO]
        
        # 添加统计
        stats = doc.add_paragraph()
        stats.add_run(f"总批注数: {len(annotations)} 条\n").bold = True
        stats.add_run(f"严重问题: {len(critical)} 条\n").font.color.rgb = RGBColor(255, 0, 0)
        stats.add_run(f"一般问题: {len(warning)} 条\n").font.color.rgb = RGBColor(255, 165, 0)
        stats.add_run(f"建议改进: {len(info)} 条").font.color.rgb = RGBColor(0, 100, 200)
        
        # 添加详细批注列表
        for severity_name, severity_list in [
            ("严重问题", critical),
            ("一般问题", warning),
            ("建议改进", info)
        ]:
            if severity_list:
                doc.add_paragraph()
                section_title = doc.add_paragraph(f"{severity_name}:")
                section_title.runs[0].bold = True
                section_title.runs[0].font.size = Pt(14)
                
                for idx, ann in enumerate(severity_list, 1):
                    doc.add_paragraph(f"{idx}. [{ann.location}] {ann.content}")

