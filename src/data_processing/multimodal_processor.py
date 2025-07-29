"""
多模态数据处理模块
"""

import numpy as np
import torch
from typing import Dict, List, Any, Tuple, Optional
import logging
from .document_parser import DocumentParser
from .image_processor import ImageProcessor
from .text_processor import TextProcessor
import re

logger = logging.getLogger(__name__)


class MultiModalProcessor:
    """多模态数据处理器"""
    
    def __init__(self):
        self.document_parser = DocumentParser()
        self.image_processor = ImageProcessor()
        self.text_processor = TextProcessor()
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        处理多模态文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            处理后的多模态数据
        """
        try:
            # 解析文档
            logger.info(f"开始解析文档: {file_path}")
            document_data = self.document_parser.parse_document(file_path)
            
            # 处理文本内容
            processed_text = self._process_text_content(document_data.get('text_content', []))
            
            # 处理图像内容
            processed_images = self._process_image_content(document_data.get('images', []))
            
            # 处理表格内容
            processed_tables = self._process_table_content(document_data.get('tables', []))
            
            # 整合多模态数据
            multimodal_data = {
                'raw_data': document_data,
                'processed_text': processed_text,
                'processed_images': processed_images,
                'processed_tables': processed_tables,
                'document_structure': self._analyze_document_structure(document_data),
                'content_alignment': self._analyze_content_alignment(processed_text, processed_images),
                'quality_metrics': self._calculate_quality_metrics(processed_text, processed_images)
            }
            
            logger.info("文档多模态处理完成")
            return multimodal_data
            
        except Exception as e:
            logger.error(f"多模态文档处理失败: {e}")
            raise
    
    def _process_text_content(self, text_content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        处理文本内容
        
        Args:
            text_content: 文本内容列表
            
        Returns:
            处理后的文本数据
        """
        try:
            # 合并所有文本
            full_text = ' '.join([item.get('content', '') for item in text_content])
            
            # 文本清理和标准化
            cleaned_text = self.text_processor.clean_text(full_text)
            normalized_text = self.text_processor.normalize_text(cleaned_text)
            
            # 文本分析
            keywords = self.text_processor.extract_keywords(normalized_text)
            entities = self.text_processor.extract_entities(normalized_text)
            sections = self.text_processor.extract_sections(normalized_text)
            grammar_errors = self.text_processor.check_grammar_errors(normalized_text)
            readability = self.text_processor.calculate_readability(normalized_text)
            
            processed_text = {
                'original_text': full_text,
                'cleaned_text': cleaned_text,
                'normalized_text': normalized_text,
                'keywords': keywords,
                'entities': entities,
                'sections': sections,
                'grammar_errors': grammar_errors,
                'readability': readability,
                'text_segments': self._segment_text_by_type(text_content),
                'statistics': {
                    'total_chars': len(full_text),
                    'total_words': len(self.text_processor.segment_text(normalized_text)),
                    'total_sentences': len(normalized_text.split('。')),
                    'paragraphs': len(text_content)
                }
            }
            
            return processed_text
            
        except Exception as e:
            logger.error(f"文本内容处理失败: {e}")
            return {}
    
    def _process_image_content(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理图像内容
        
        Args:
            images: 图像列表
            
        Returns:
            处理后的图像数据
        """
        processed_images = []
        
        for i, image_data in enumerate(images):
            try:
                # 预处理图像
                img_array = self.image_processor.preprocess_image(image_data['data'])
                
                # 图像分析
                layout_analysis = self.image_processor.analyze_layout(img_array)
                text_regions = self.image_processor.extract_text_regions(img_array)
                signatures = self.image_processor.detect_signatures(img_array)
                tables = self.image_processor.detect_tables(img_array)
                
                # OCR文字识别
                ocr_text = self.document_parser.extract_text_from_image(image_data['data'])
                
                processed_image = {
                    'index': i,
                    'filename': image_data.get('filename', f'image_{i}'),
                    'original_data': image_data,
                    'layout_analysis': layout_analysis,
                    'text_regions': text_regions,
                    'signatures': signatures,
                    'tables': tables,
                    'ocr_text': ocr_text,
                    'ocr_entities': self.text_processor.extract_entities(ocr_text) if ocr_text else {},
                    'image_features': self._extract_image_features(img_array)
                }
                
                processed_images.append(processed_image)
                
            except Exception as e:
                logger.error(f"处理第{i}张图像失败: {e}")
                continue
        
        return processed_images
    
    def _process_table_content(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理表格内容
        
        Args:
            tables: 表格列表
            
        Returns:
            处理后的表格数据
        """
        processed_tables = []
        
        for i, table_data in enumerate(tables):
            try:
                table_array = table_data.get('data', [])
                
                if not table_array:
                    continue
                
                # 表格结构分析
                structure_analysis = self._analyze_table_structure(table_array)
                
                # 表格内容分析
                content_analysis = self._analyze_table_content(table_array)
                
                processed_table = {
                    'index': i,
                    'original_data': table_data,
                    'structure': structure_analysis,
                    'content': content_analysis,
                    'entities': self._extract_table_entities(table_array),
                    'quality_score': self._calculate_table_quality(table_array)
                }
                
                processed_tables.append(processed_table)
                
            except Exception as e:
                logger.error(f"处理第{i}个表格失败: {e}")
                continue
        
        return processed_tables
    
    def _segment_text_by_type(self, text_content: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        按类型分割文本
        
        Args:
            text_content: 文本内容列表
            
        Returns:
            按类型分组的文本
        """
        segments = {
            'paragraphs': [],
            'pages': [],
            'titles': [],
            'other': []
        }
        
        for item in text_content:
            content = item.get('content', '')
            content_type = item.get('type', 'other')
            
            if content_type == 'paragraph':
                segments['paragraphs'].append(content)
            elif content_type == 'page':
                segments['pages'].append(content)
            elif content_type in ['title', 'heading']:
                segments['titles'].append(content)
            else:
                segments['other'].append(content)
        
        return segments
    
    def _extract_image_features(self, img_array: np.ndarray) -> Dict[str, Any]:
        """
        提取图像特征
        
        Args:
            img_array: 图像数组
            
        Returns:
            图像特征
        """
        try:
            # 基础图像特征
            height, width = img_array.shape[:2]
            
            # 颜色统计
            mean_color = np.mean(img_array, axis=(0, 1))
            
            # 亮度统计
            gray = np.mean(img_array, axis=2)
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            features = {
                'dimensions': (width, height),
                'aspect_ratio': width / height,
                'mean_color': mean_color.tolist(),
                'brightness': brightness,
                'contrast': contrast,
                'has_color': np.std(img_array) > 10  # 简单的彩色检测
            }
            
            return features
            
        except Exception as e:
            logger.error(f"图像特征提取失败: {e}")
            return {}
    
    def _analyze_table_structure(self, table_array: List[List[str]]) -> Dict[str, Any]:
        """
        分析表格结构
        
        Args:
            table_array: 表格数据数组
            
        Returns:
            表格结构分析
        """
        if not table_array:
            return {}
        
        rows = len(table_array)
        cols = len(table_array[0]) if table_array else 0
        
        # 检查表格一致性
        consistent_cols = all(len(row) == cols for row in table_array)
        
        # 检查空单元格
        empty_cells = 0
        total_cells = 0
        
        for row in table_array:
            for cell in row:
                total_cells += 1
                if not cell.strip():
                    empty_cells += 1
        
        structure = {
            'rows': rows,
            'columns': cols,
            'total_cells': total_cells,
            'empty_cells': empty_cells,
            'empty_ratio': empty_cells / total_cells if total_cells > 0 else 0,
            'is_consistent': consistent_cols,
            'has_header': self._has_table_header(table_array)
        }
        
        return structure
    
    def _analyze_table_content(self, table_array: List[List[str]]) -> Dict[str, Any]:
        """
        分析表格内容
        
        Args:
            table_array: 表格数据数组
            
        Returns:
            表格内容分析
        """
        if not table_array:
            return {}
        
        # 合并所有单元格内容
        all_text = ' '.join([' '.join(row) for row in table_array])
        
        # 检测数据类型
        numeric_cells = 0
        text_cells = 0
        date_cells = 0
        
        for row in table_array:
            for cell in row:
                cell = cell.strip()
                if not cell:
                    continue
                
                # 数字检测
                if re.match(r'^[\d\.\-\+]+$', cell):
                    numeric_cells += 1
                # 日期检测
                elif re.match(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}', cell):
                    date_cells += 1
                else:
                    text_cells += 1
        
        total_content_cells = numeric_cells + text_cells + date_cells
        
        content = {
            'total_content': all_text,
            'content_types': {
                'numeric': numeric_cells,
                'text': text_cells,
                'date': date_cells
            },
            'content_distribution': {
                'numeric_ratio': numeric_cells / total_content_cells if total_content_cells > 0 else 0,
                'text_ratio': text_cells / total_content_cells if total_content_cells > 0 else 0,
                'date_ratio': date_cells / total_content_cells if total_content_cells > 0 else 0
            }
        }
        
        return content
    
    def _extract_table_entities(self, table_array: List[List[str]]) -> Dict[str, List[str]]:
        """
        从表格中提取实体
        
        Args:
            table_array: 表格数据数组
            
        Returns:
            实体字典
        """
        # 合并表格内容
        table_text = ' '.join([' '.join(row) for row in table_array])
        
        # 使用文本处理器提取实体
        return self.text_processor.extract_entities(table_text)
    
    def _has_table_header(self, table_array: List[List[str]]) -> bool:
        """
        检查表格是否有表头
        
        Args:
            table_array: 表格数据数组
            
        Returns:
            是否有表头
        """
        if len(table_array) < 2:
            return False
        
        # 简单检测：第一行是否包含常见表头关键词
        first_row = ' '.join(table_array[0])
        header_keywords = ['名称', '编号', '时间', '数量', '类型', '状态', '备注', '说明', '要求']
        
        return any(keyword in first_row for keyword in header_keywords)
    
    def _calculate_table_quality(self, table_array: List[List[str]]) -> float:
        """
        计算表格质量分数
        
        Args:
            table_array: 表格数据数组
            
        Returns:
            质量分数 (0-1)
        """
        if not table_array:
            return 0.0
        
        # 计算完整性
        total_cells = sum(len(row) for row in table_array)
        empty_cells = sum(1 for row in table_array for cell in row if not cell.strip())
        completeness = 1 - (empty_cells / total_cells) if total_cells > 0 else 0
        
        # 计算一致性
        expected_cols = len(table_array[0]) if table_array else 0
        consistent_rows = sum(1 for row in table_array if len(row) == expected_cols)
        consistency = consistent_rows / len(table_array) if table_array else 0
        
        # 综合质量分数
        quality_score = (completeness * 0.6 + consistency * 0.4)
        
        return quality_score
    
    def _analyze_document_structure(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析文档结构
        
        Args:
            document_data: 文档数据
            
        Returns:
            文档结构分析
        """
        structure = {
            'total_pages': document_data.get('total_pages', 0),
            'file_type': document_data.get('file_type', 'unknown'),
            'has_images': len(document_data.get('images', [])) > 0,
            'has_tables': len(document_data.get('tables', [])) > 0,
            'text_sections': len(document_data.get('text_content', [])),
            'image_count': len(document_data.get('images', [])),
            'table_count': len(document_data.get('tables', []))
        }
        
        return structure
    
    def _analyze_content_alignment(self, processed_text: Dict[str, Any], processed_images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析内容对齐情况
        
        Args:
            processed_text: 处理后的文本数据
            processed_images: 处理后的图像数据
            
        Returns:
            内容对齐分析
        """
        alignment = {
            'text_image_consistency': 0.0,
            'reference_completeness': 0.0,
            'annotation_accuracy': 0.0
        }
        
        try:
            # 提取文本中的关键词
            text_keywords = set([kw[0] for kw in processed_text.get('keywords', [])])
            
            # 提取图像OCR文字中的关键词
            image_keywords = set()
            for img in processed_images:
                ocr_text = img.get('ocr_text', '')
                if ocr_text:
                    img_keywords = self.text_processor.extract_keywords(ocr_text)
                    image_keywords.update([kw[0] for kw in img_keywords])
            
            # 计算文本-图像一致性
            if text_keywords and image_keywords:
                common_keywords = text_keywords.intersection(image_keywords)
                consistency = len(common_keywords) / len(text_keywords.union(image_keywords))
                alignment['text_image_consistency'] = consistency
            
            # 其他对齐指标可以进一步实现
            
        except Exception as e:
            logger.error(f"内容对齐分析失败: {e}")
        
        return alignment
    
    def _calculate_quality_metrics(self, processed_text: Dict[str, Any], processed_images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算质量指标
        
        Args:
            processed_text: 处理后的文本数据
            processed_images: 处理后的图像数据
            
        Returns:
            质量指标
        """
        metrics = {
            'text_quality': 0.0,
            'image_quality': 0.0,
            'overall_quality': 0.0
        }
        
        try:
            # 文本质量
            readability = processed_text.get('readability', {})
            text_score = readability.get('score', 0) / 100
            grammar_errors = len(processed_text.get('grammar_errors', []))
            text_quality = max(0, text_score - grammar_errors * 0.05)
            metrics['text_quality'] = text_quality
            
            # 图像质量
            if processed_images:
                image_scores = []
                for img in processed_images:
                    layout_analysis = img.get('layout_analysis', {})
                    quality_score = layout_analysis.get('quality_score', 0)
                    image_scores.append(quality_score)
                
                metrics['image_quality'] = np.mean(image_scores) if image_scores else 0
            
            # 总体质量
            metrics['overall_quality'] = (metrics['text_quality'] + metrics['image_quality']) / 2
            
        except Exception as e:
            logger.error(f"质量指标计算失败: {e}")
        
        return metrics 