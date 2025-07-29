"""
版面分析模型
"""

import torch
import torch.nn as nn
import cv2
import numpy as np
from typing import Dict, List, Any, Tuple
import logging
from .base_model import BaseModel

logger = logging.getLogger(__name__)


class LayoutAnalyzer(BaseModel):
    """版面分析器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self.num_classes = len(config.get('classes', ['text', 'image', 'table', 'title']))
        self.class_names = config.get('classes', ['text', 'image', 'table', 'title'])
        
        # 简化的语义分割网络
        self.encoder = self._build_encoder()
        self.decoder = self._build_decoder()
        
    def _build_encoder(self):
        """构建编码器"""
        return nn.Sequential(
            # 第一层
            nn.Conv2d(3, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            # 第二层
            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            # 第三层
            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            # 第四层
            nn.Conv2d(256, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, 3, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True)
        )
    
    def _build_decoder(self):
        """构建解码器"""
        return nn.Sequential(
            # 上采样层
            nn.ConvTranspose2d(512, 256, 2, stride=2),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            
            nn.ConvTranspose2d(256, 128, 2, stride=2),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            
            nn.ConvTranspose2d(128, 64, 2, stride=2),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            
            # 最终分类层
            nn.Conv2d(64, self.num_classes, 1)
        )
    
    def forward(self, x):
        """前向传播"""
        # 编码
        features = self.encoder(x)
        
        # 解码
        output = self.decoder(features)
        
        return output
    
    def predict(self, image_data: bytes) -> Dict[str, Any]:
        """
        分析图像版面布局
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            版面分析结果
        """
        try:
            # 预处理图像
            img_tensor, original_size = self._preprocess_image(image_data)
            
            # 模型推理
            self.eval()
            with torch.no_grad():
                output = self.forward(img_tensor)
                # 获取预测结果
                predictions = torch.softmax(output, dim=1)
                segmentation_map = predictions.argmax(dim=1).squeeze().cpu().numpy()
            
            # 后处理：调整回原始尺寸
            segmentation_map = cv2.resize(segmentation_map.astype(np.uint8), original_size, 
                                        interpolation=cv2.INTER_NEAREST)
            
            # 提取各类区域
            layout_regions = self._extract_layout_regions(segmentation_map)
            
            # 传统方法作为补充
            traditional_result = self._traditional_layout_analysis(image_data)
            
            # 合并结果
            final_result = self._merge_results(layout_regions, traditional_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"版面分析失败: {e}")
            return {
                'regions': [],
                'statistics': {},
                'error': str(e)
            }
    
    def _preprocess_image(self, image_data: bytes) -> Tuple[torch.Tensor, Tuple[int, int]]:
        """
        预处理图像
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            预处理后的张量和原始尺寸
        """
        # 解码图像
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("无法解码图像")
        
        original_size = (img.shape[1], img.shape[0])  # (width, height)
        
        # 调整大小
        img = cv2.resize(img, (512, 512))
        
        # BGR转RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 归一化
        img = img.astype(np.float32) / 255.0
        
        # 转换为张量
        img_tensor = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0)  # (1, 3, H, W)
        img_tensor = img_tensor.to(self.device)
        
        return img_tensor, original_size
    
    def _extract_layout_regions(self, segmentation_map: np.ndarray) -> List[Dict[str, Any]]:
        """
        从分割图中提取版面区域
        
        Args:
            segmentation_map: 分割结果图
            
        Returns:
            版面区域列表
        """
        regions = []
        
        for class_id, class_name in enumerate(self.class_names):
            # 获取当前类别的掩码
            mask = (segmentation_map == class_id).astype(np.uint8)
            
            # 查找轮廓
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # 过滤太小的区域
                if area < 100:
                    continue
                
                # 获取边界框
                x, y, w, h = cv2.boundingRect(contour)
                
                # 计算置信度（基于区域大小和形状）
                confidence = min(1.0, area / 10000)  # 简化的置信度计算
                
                regions.append({
                    'type': class_name,
                    'bbox': (x, y, w, h),
                    'area': area,
                    'confidence': confidence,
                    'contour': contour.tolist()
                })
        
        return regions
    
    def _traditional_layout_analysis(self, image_data: bytes) -> Dict[str, Any]:
        """
        传统方法进行版面分析
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            分析结果
        """
        try:
            # 解码图像
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {'regions': [], 'statistics': {}}
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 检测文本区域
            text_regions = self._detect_text_regions(gray)
            
            # 检测表格
            table_regions = self._detect_table_regions(gray)
            
            # 检测图像区域
            image_regions = self._detect_image_regions(gray)
            
            # 合并所有区域
            all_regions = []
            all_regions.extend([{**r, 'type': 'text'} for r in text_regions])
            all_regions.extend([{**r, 'type': 'table'} for r in table_regions])
            all_regions.extend([{**r, 'type': 'image'} for r in image_regions])
            
            # 计算统计信息
            statistics = self._calculate_layout_statistics(all_regions, img.shape)
            
            return {
                'regions': all_regions,
                'statistics': statistics
            }
            
        except Exception as e:
            logger.error(f"传统版面分析失败: {e}")
            return {'regions': [], 'statistics': {}}
    
    def _detect_text_regions(self, gray: np.ndarray) -> List[Dict[str, Any]]:
        """检测文本区域"""
        # 形态学操作检测文本行
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
        dilated = cv2.dilate(gray, kernel, iterations=1)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # 文本行特征：宽度较大，高度较小
            if w > 50 and h > 5 and w/h > 3:
                text_regions.append({
                    'bbox': (x, y, w, h),
                    'area': w * h,
                    'confidence': 0.7
                })
        
        return text_regions
    
    def _detect_table_regions(self, gray: np.ndarray) -> List[Dict[str, Any]]:
        """检测表格区域"""
        # 检测水平线
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
        
        # 检测垂直线
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
        
        # 合并线条
        table_structure = cv2.add(horizontal_lines, vertical_lines)
        
        contours, _ = cv2.findContours(table_structure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        table_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:
                x, y, w, h = cv2.boundingRect(contour)
                table_regions.append({
                    'bbox': (x, y, w, h),
                    'area': area,
                    'confidence': 0.8
                })
        
        return table_regions
    
    def _detect_image_regions(self, gray: np.ndarray) -> List[Dict[str, Any]]:
        """检测图像区域"""
        # 使用边缘检测和轮廓分析
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        image_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 5000:  # 图像区域通常较大
                x, y, w, h = cv2.boundingRect(contour)
                
                # 检查宽高比，图像通常比较方正
                aspect_ratio = w / h
                if 0.5 <= aspect_ratio <= 2.0:
                    image_regions.append({
                        'bbox': (x, y, w, h),
                        'area': area,
                        'confidence': 0.6
                    })
        
        return image_regions
    
    def _calculate_layout_statistics(self, regions: List[Dict[str, Any]], image_shape: Tuple[int, int, int]) -> Dict[str, Any]:
        """计算版面统计信息"""
        height, width = image_shape[:2]
        total_area = height * width
        
        type_counts = {}
        type_areas = {}
        
        for region in regions:
            region_type = region['type']
            area = region['area']
            
            type_counts[region_type] = type_counts.get(region_type, 0) + 1
            type_areas[region_type] = type_areas.get(region_type, 0) + area
        
        statistics = {
            'total_regions': len(regions),
            'image_size': (width, height),
            'region_counts': type_counts,
            'area_coverage': {
                region_type: area / total_area 
                for region_type, area in type_areas.items()
            },
            'layout_complexity': len(regions) / 10.0  # 简化的复杂度计算
        }
        
        return statistics
    
    def _merge_results(self, ml_regions: List[Dict[str, Any]], traditional_result: Dict[str, Any]) -> Dict[str, Any]:
        """合并机器学习和传统方法的结果"""
        # 简单合并策略：优先使用机器学习结果，传统方法作为补充
        all_regions = ml_regions.copy()
        traditional_regions = traditional_result.get('regions', [])
        
        # 添加传统方法检测到但机器学习没有检测到的区域
        for trad_region in traditional_regions:
            # 检查是否与现有区域重叠
            is_duplicate = False
            for ml_region in ml_regions:
                if self._regions_overlap(trad_region['bbox'], ml_region['bbox']):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                all_regions.append(trad_region)
        
        # 重新计算统计信息
        statistics = traditional_result.get('statistics', {})
        
        return {
            'regions': all_regions,
            'statistics': statistics,
            'region_count': len(all_regions)
        }
    
    def _regions_overlap(self, bbox1: Tuple[int, int, int, int], bbox2: Tuple[int, int, int, int], threshold: float = 0.3) -> bool:
        """检查两个区域是否重叠"""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # 计算IoU
        inter_x1 = max(x1, x2)
        inter_y1 = max(y1, y2)
        inter_x2 = min(x1 + w1, x2 + w2)
        inter_y2 = min(y1 + h1, y2 + h2)
        
        if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
            return False
        
        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        union_area = w1 * h1 + w2 * h2 - inter_area
        
        iou = inter_area / union_area if union_area > 0 else 0
        
        return iou > threshold 