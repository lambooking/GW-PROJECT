"""
图像处理模块
"""

import cv2
import numpy as np
from PIL import Image
import io
from typing import List, Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """图像处理器"""
    
    def __init__(self, max_size: int = 1920, quality_threshold: float = 0.8):
        self.max_size = max_size
        self.quality_threshold = quality_threshold
    
    def preprocess_image(self, image_data: bytes) -> np.ndarray:
        """
        预处理图像
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            处理后的图像数组
        """
        try:
            # 将字节数据转换为numpy数组
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValueError("无法解码图像数据")
            
            # 调整图像大小
            img = self._resize_image(img)
            
            # 图像增强
            img = self._enhance_image(img)
            
            return img
            
        except Exception as e:
            logger.error(f"图像预处理失败: {e}")
            raise
    
    def _resize_image(self, img: np.ndarray) -> np.ndarray:
        """
        调整图像大小
        
        Args:
            img: 输入图像
            
        Returns:
            调整大小后的图像
        """
        height, width = img.shape[:2]
        
        # 如果图像尺寸小于最大尺寸，直接返回
        if max(height, width) <= self.max_size:
            return img
        
        # 计算缩放比例
        if width > height:
            new_width = self.max_size
            new_height = int(height * self.max_size / width)
        else:
            new_height = self.max_size
            new_width = int(width * self.max_size / height)
        
        # 调整大小
        resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return resized_img
    
    def _enhance_image(self, img: np.ndarray) -> np.ndarray:
        """
        图像增强
        
        Args:
            img: 输入图像
            
        Returns:
            增强后的图像
        """
        # 转换为LAB色彩空间
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # 应用CLAHE（对比度限制的自适应直方图均衡化）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # 合并通道并转换回BGR
        enhanced_lab = cv2.merge([l, a, b])
        enhanced_img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        return enhanced_img
    
    def detect_image_quality(self, img: np.ndarray) -> float:
        """
        检测图像质量
        
        Args:
            img: 输入图像
            
        Returns:
            图像质量分数 (0-1)
        """
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 计算拉普拉斯方差（衡量清晰度）
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # 计算梯度强度
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            avg_gradient = np.mean(gradient_magnitude)
            
            # 计算对比度
            contrast = gray.std()
            
            # 综合评分
            quality_score = min(1.0, (laplacian_var / 1000 + avg_gradient / 100 + contrast / 100) / 3)
            
            return quality_score
            
        except Exception as e:
            logger.error(f"图像质量检测失败: {e}")
            return 0.0
    
    def extract_text_regions(self, img: np.ndarray) -> List[Dict[str, Any]]:
        """
        提取文本区域
        
        Args:
            img: 输入图像
            
        Returns:
            文本区域列表
        """
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 应用形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
            dilated = cv2.dilate(gray, kernel, iterations=1)
            
            # 查找轮廓
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_regions = []
            for contour in contours:
                # 计算边界框
                x, y, w, h = cv2.boundingRect(contour)
                
                # 过滤小区域
                if w < 50 or h < 10:
                    continue
                
                # 计算宽高比
                aspect_ratio = w / h
                
                # 过滤非文本区域
                if aspect_ratio < 2 or aspect_ratio > 20:
                    continue
                
                text_regions.append({
                    'bbox': (x, y, w, h),
                    'area': w * h,
                    'aspect_ratio': aspect_ratio
                })
            
            # 按面积排序
            text_regions.sort(key=lambda x: x['area'], reverse=True)
            
            return text_regions
            
        except Exception as e:
            logger.error(f"文本区域提取失败: {e}")
            return []
    
    def detect_signatures(self, img: np.ndarray) -> List[Dict[str, Any]]:
        """
        检测手写签名
        
        Args:
            img: 输入图像
            
        Returns:
            签名区域列表
        """
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 边缘检测
            edges = cv2.Canny(gray, 50, 150)
            
            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            signatures = []
            for contour in contours:
                # 计算轮廓特征
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                
                # 过滤小轮廓
                if area < 500:
                    continue
                
                # 计算复杂度（周长平方/面积）
                if perimeter > 0:
                    complexity = (perimeter ** 2) / area
                else:
                    continue
                
                # 签名通常具有较高的复杂度
                if complexity > 25:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    signatures.append({
                        'bbox': (x, y, w, h),
                        'area': area,
                        'complexity': complexity,
                        'confidence': min(1.0, complexity / 100)
                    })
            
            # 按置信度排序
            signatures.sort(key=lambda x: x['confidence'], reverse=True)
            
            return signatures
            
        except Exception as e:
            logger.error(f"签名检测失败: {e}")
            return []
    
    def detect_tables(self, img: np.ndarray) -> List[Dict[str, Any]]:
        """
        检测表格区域
        
        Args:
            img: 输入图像
            
        Returns:
            表格区域列表
        """
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 检测水平线
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            
            # 检测垂直线
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
            
            # 合并水平线和垂直线
            table_structure = cv2.add(horizontal_lines, vertical_lines)
            
            # 查找轮廓
            contours, _ = cv2.findContours(table_structure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            tables = []
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # 过滤小区域
                if area < 1000:
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                
                # 检查宽高比，表格通常比较规整
                aspect_ratio = w / h
                if 0.3 <= aspect_ratio <= 3.0:
                    tables.append({
                        'bbox': (x, y, w, h),
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    })
            
            # 按面积排序
            tables.sort(key=lambda x: x['area'], reverse=True)
            
            return tables
            
        except Exception as e:
            logger.error(f"表格检测失败: {e}")
            return []
    
    def analyze_layout(self, img: np.ndarray) -> Dict[str, Any]:
        """
        分析图像版面布局
        
        Args:
            img: 输入图像
            
        Returns:
            版面分析结果
        """
        try:
            # 获取图像尺寸
            height, width = img.shape[:2]
            
            # 检测各类元素
            text_regions = self.extract_text_regions(img)
            signatures = self.detect_signatures(img)
            tables = self.detect_tables(img)
            
            # 计算覆盖面积
            total_area = height * width
            text_area = sum(region['area'] for region in text_regions)
            table_area = sum(table['area'] for table in tables)
            
            layout_analysis = {
                'image_size': (width, height),
                'total_area': total_area,
                'text_regions': len(text_regions),
                'text_coverage': text_area / total_area if total_area > 0 else 0,
                'signatures': len(signatures),
                'tables': len(tables),
                'table_coverage': table_area / total_area if total_area > 0 else 0,
                'quality_score': self.detect_image_quality(img),
                'layout_complexity': self._calculate_layout_complexity(text_regions, signatures, tables)
            }
            
            return layout_analysis
            
        except Exception as e:
            logger.error(f"版面分析失败: {e}")
            return {}
    
    def _calculate_layout_complexity(self, text_regions: List[Dict], signatures: List[Dict], tables: List[Dict]) -> float:
        """
        计算版面复杂度
        
        Args:
            text_regions: 文本区域
            signatures: 签名区域
            tables: 表格区域
            
        Returns:
            复杂度分数
        """
        # 基于元素数量和分布计算复杂度
        total_elements = len(text_regions) + len(signatures) + len(tables)
        
        # 归一化复杂度分数
        complexity = min(1.0, total_elements / 20)
        
        return complexity
    
    def convert_to_pil(self, img: np.ndarray) -> Image.Image:
        """
        将OpenCV图像转换为PIL图像
        
        Args:
            img: OpenCV图像（BGR格式）
            
        Returns:
            PIL图像
        """
        # 转换颜色格式 BGR -> RGB
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 转换为PIL图像
        pil_img = Image.fromarray(rgb_img)
        
        return pil_img
    
    def save_processed_image(self, img: np.ndarray, output_path: str) -> bool:
        """
        保存处理后的图像
        
        Args:
            img: 处理后的图像
            output_path: 输出路径
            
        Returns:
            是否保存成功
        """
        try:
            cv2.imwrite(output_path, img)
            logger.info(f"图像保存成功: {output_path}")
            return True
        except Exception as e:
            logger.error(f"图像保存失败: {e}")
            return False 