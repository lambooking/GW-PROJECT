"""
数据预处理模块 - 为竞赛文档分析系统提供完整的数据预处理能力

主要组件：
1. DocumentParser - 基础文档解析器
2. EnhancedPDFParser - 增强PDF解析器  
3. DocumentClassifier - 文档分类器
4. StructuredDataExtractor - 结构化数据提取器
5. MultimodalFusion - 多模态内容融合器
6. EntityExtractor - 实体提取与标注器
7. PreprocessingPipeline - 综合预处理管道

使用示例：
    from src.data_processing import PreprocessingPipeline
    
    pipeline = PreprocessingPipeline()
    result = pipeline.process_document("path/to/document.pdf")
"""

from .document_parser import DocumentParser
from .enhanced_pdf_parser import EnhancedPDFParser
from .document_classifier import DocumentClassifier
from .structured_data_extractor import StructuredDataExtractor
from .multimodal_fusion import MultimodalFusion
from .entity_extractor import EntityExtractor
from .preprocessing_pipeline import PreprocessingPipeline

__all__ = [
    'DocumentParser',
    'EnhancedPDFParser', 
    'DocumentClassifier',
    'StructuredDataExtractor',
    'MultimodalFusion',
    'EntityExtractor',
    'PreprocessingPipeline'
]

__version__ = '1.0.0'