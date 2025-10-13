"""
批注器基类
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union

from .schemas import Annotation, AnnotationCollection

logger = logging.getLogger(__name__)


class BaseAnnotator(ABC):
    """批注器基类"""
    
    def __init__(self):
        """初始化批注器"""
        self.supported_extensions = []
    
    @abstractmethod
    def annotate(
        self, 
        input_file: Union[str, Path],
        annotations: List[Annotation],
        output_file: Union[str, Path]
    ) -> Path:
        """
        在文档上添加批注
        
        Args:
            input_file: 输入文件路径
            annotations: 批注列表
            output_file: 输出文件路径
            
        Returns:
            输出文件路径
        """
        pass
    
    def supports_format(self, file_path: Union[str, Path]) -> bool:
        """检查是否支持该文件格式"""
        file_path = Path(file_path)
        return file_path.suffix.lower() in self.supported_extensions
    
    def _validate_file(self, file_path: Union[str, Path]) -> Path:
        """验证文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not self.supports_format(file_path):
            raise ValueError(
                f"不支持的文件格式: {file_path.suffix}. "
                f"支持的格式: {self.supported_extensions}"
            )
        
        return file_path
    
    def _sort_annotations_by_page(self, annotations: List[Annotation]) -> dict:
        """按页码排序批注"""
        page_annotations = {}
        for ann in annotations:
            page_num = ann.page_number
            if page_num not in page_annotations:
                page_annotations[page_num] = []
            page_annotations[page_num].append(ann)
        
        return page_annotations
    
    def _log_annotation_stats(self, annotations: List[Annotation]) -> None:
        """记录批注统计信息"""
        if not annotations:
            logger.warning("没有批注需要添加")
            return
        
        critical = sum(1 for a in annotations if a.severity == "critical")
        warning = sum(1 for a in annotations if a.severity == "warning")
        info = sum(1 for a in annotations if a.severity == "info")
        
        logger.info(
            f"批注统计: 总计 {len(annotations)} 条 "
            f"(严重: {critical}, 警告: {warning}, 建议: {info})"
        )


