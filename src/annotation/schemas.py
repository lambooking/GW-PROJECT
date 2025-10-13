"""
批注系统数据结构定义
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AnnotationSeverity(str, Enum):
    """批注严重程度"""
    CRITICAL = "critical"  # 严重问题，扣分>5
    WARNING = "warning"    # 一般问题，扣分2-5
    INFO = "info"          # 建议改进，扣分<2


class AnnotationType(str, Enum):
    """批注类型"""
    COMMENT = "comment"           # 批注评论
    HIGHLIGHT = "highlight"       # 高亮标记
    SUGGESTION = "suggestion"     # 修改建议
    MISSING = "missing"           # 缺失内容


class Annotation(BaseModel):
    """批注数据结构"""
    
    # 位置信息
    location: str = Field(description="位置描述，如'第2页 第3段'或'第1.2节'")
    page_number: int = Field(description="页码")
    coordinates: Optional[Dict[str, float]] = Field(None, description="坐标信息 {x0, y0, x1, y1}")
    
    # 批注信息
    annotation_type: AnnotationType = Field(description="批注类型")
    severity: AnnotationSeverity = Field(description="严重程度")
    score_item: str = Field(description="关联的评分项名称")
    
    # 内容
    content: str = Field(description="批注文本内容")
    suggestion: Optional[str] = Field(None, description="修改建议")
    
    # 评分信息
    score_lost: float = Field(default=0.0, description="扣分值")
    max_score: float = Field(default=0.0, description="该项满分")
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    author: str = Field(default="RAG智能评分系统", description="批注作者")
    
    # 匹配信息（用于定位）
    text_snippet: Optional[str] = Field(None, description="文本片段，用于匹配定位")
    section_name: Optional[str] = Field(None, description="章节名称")
    
    def get_color_code(self) -> tuple:
        """获取颜色代码 (RGB)"""
        if self.severity == AnnotationSeverity.CRITICAL:
            return (1.0, 0.0, 0.0)  # 红色
        elif self.severity == AnnotationSeverity.WARNING:
            return (1.0, 0.84, 0.0)  # 金色/黄色
        else:
            return (0.0, 0.5, 1.0)  # 蓝色
    
    def get_formatted_content(self) -> str:
        """获取格式化的批注内容"""
        lines = [
            f"【{self.score_item}】",
            f"扣分: {self.score_lost:.1f}/{self.max_score:.1f}分",
            f"",
            f"问题: {self.content}"
        ]
        
        if self.suggestion:
            lines.append(f"")
            lines.append(f"修改建议: {self.suggestion}")
        
        return "\n".join(lines)
    
    class Config:
        use_enum_values = True


class AnnotationCollection(BaseModel):
    """批注集合"""
    
    annotations: List[Annotation] = Field(default_factory=list, description="批注列表")
    document_name: str = Field(description="文档名称")
    total_annotations: int = Field(default=0, description="批注总数")
    
    critical_count: int = Field(default=0, description="严重问题数")
    warning_count: int = Field(default=0, description="一般问题数")
    info_count: int = Field(default=0, description="建议改进数")
    
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    def add_annotation(self, annotation: Annotation) -> None:
        """添加批注"""
        self.annotations.append(annotation)
        self.total_annotations += 1
        
        if annotation.severity == AnnotationSeverity.CRITICAL:
            self.critical_count += 1
        elif annotation.severity == AnnotationSeverity.WARNING:
            self.warning_count += 1
        else:
            self.info_count += 1
    
    def get_annotations_by_page(self, page_number: int) -> List[Annotation]:
        """获取指定页的批注"""
        return [ann for ann in self.annotations if ann.page_number == page_number]
    
    def get_annotations_by_severity(self, severity: AnnotationSeverity) -> List[Annotation]:
        """获取指定严重程度的批注"""
        return [ann for ann in self.annotations if ann.severity == severity]


