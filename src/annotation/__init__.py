"""
文档批注模块 - 支持PDF和DOCX格式的智能批注
"""

from .schemas import Annotation, AnnotationSeverity, AnnotationType
from .manager import AnnotationManager
from .docx_annotator import DocxAnnotator
from .pdf_annotator import PdfAnnotator

__all__ = [
    'Annotation',
    'AnnotationSeverity',
    'AnnotationType',
    'AnnotationManager',
    'DocxAnnotator',
    'PdfAnnotator'
]

