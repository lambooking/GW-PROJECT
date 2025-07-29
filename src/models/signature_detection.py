"""
签名检测模型
"""

import torch
import torch.nn as nn
import cv2
import numpy as np
from typing import Dict, List, Any, Tuple
import logging
from .base_model import BaseModel

logger = logging.getLogger(__name__)


class SignatureDetector(BaseModel):
    """签名检测器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 简化的CNN网络用于签名检测
        self.backbone = nn.Sequential(
            # 第一个卷积块
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            # 第二个卷积块
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            # 第三个卷积块
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            
            # 第四个卷积块
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((4, 4))
        )
        
        # 分类头
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 4 * 4, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(128, 2)  # 二分类：有签名/无签名
        )
        
        self.confidence_threshold = config.get('confidence_threshold', 0.8)
    
    def forward(self, x):
        """前向传播"""
        features = self.backbone(x)
        logits = self.classifier(features)
        return logits
    
    def predict(self, image_data: bytes) -> Dict[str, Any]:
        """
        预测图像中是否有签名
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            检测结果
        """
        try:
            # 预处理图像
            img_tensor = self._preprocess_image(image_data)
            
            # 模型推理
            self.eval()
            with torch.no_grad():
                logits = self.forward(img_tensor)
                probabilities = torch.softmax(logits, dim=1)
                confidence = probabilities.max().item()
                predicted_class = probabilities.argmax().item()
            
            # 传统CV方法作为备选
            traditional_result = self._traditional_signature_detection(image_data)
            
            # 综合判断
            has_signature = (predicted_class == 1 and confidence > self.confidence_threshold) or \
                          traditional_result['has_signature']
            
            final_confidence = max(confidence, traditional_result['confidence'])
            
            return {
                'has_signature': has_signature,
                'confidence': final_confidence,
                'ml_prediction': {
                    'class': predicted_class,
                    'confidence': confidence
                },
                'traditional_prediction': traditional_result,
                'signature_regions': traditional_result.get('regions', [])
            }
            
        except Exception as e:
            logger.error(f"签名检测失败: {e}")
            return {
                'has_signature': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _preprocess_image(self, image_data: bytes) -> torch.Tensor:
        """
        预处理图像
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            预处理后的张量
        """
        # 解码图像
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            raise ValueError("无法解码图像")
        
        # 调整大小到固定尺寸
        img = cv2.resize(img, (224, 224))
        
        # 归一化
        img = img.astype(np.float32) / 255.0
        
        # 转换为张量
        img_tensor = torch.from_numpy(img).unsqueeze(0).unsqueeze(0)  # (1, 1, H, W)
        img_tensor = img_tensor.to(self.device)
        
        return img_tensor
    
    def _traditional_signature_detection(self, image_data: bytes) -> Dict[str, Any]:
        """
        传统CV方法检测签名
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            检测结果
        """
        try:
            # 解码图像
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {'has_signature': False, 'confidence': 0.0, 'regions': []}
            
            # 转为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 边缘检测
            edges = cv2.Canny(gray, 50, 150)
            
            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            signature_regions = []
            total_signature_score = 0
            
            for contour in contours:
                # 计算轮廓特征
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                
                # 过滤太小的轮廓
                if area < 500:
                    continue
                
                # 计算复杂度
                if perimeter > 0:
                    complexity = (perimeter ** 2) / area
                else:
                    continue
                
                # 计算密度
                x, y, w, h = cv2.boundingRect(contour)
                rect_area = w * h
                density = area / rect_area if rect_area > 0 else 0
                
                # 签名特征：复杂度高、密度适中
                if complexity > 25 and 0.1 < density < 0.8:
                    confidence = min(1.0, (complexity / 100) * density * 2)
                    
                    signature_regions.append({
                        'bbox': (x, y, w, h),
                        'area': area,
                        'complexity': complexity,
                        'density': density,
                        'confidence': confidence
                    })
                    
                    total_signature_score += confidence
            
            # 排序并取置信度最高的区域
            signature_regions.sort(key=lambda x: x['confidence'], reverse=True)
            
            # 判断是否有签名
            has_signature = len(signature_regions) > 0 and signature_regions[0]['confidence'] > 0.3
            final_confidence = signature_regions[0]['confidence'] if signature_regions else 0.0
            
            return {
                'has_signature': has_signature,
                'confidence': final_confidence,
                'regions': signature_regions[:5],  # 最多返回5个候选区域
                'total_regions': len(signature_regions)
            }
            
        except Exception as e:
            logger.error(f"传统签名检测失败: {e}")
            return {'has_signature': False, 'confidence': 0.0, 'regions': []}
    
    def detect_multiple_signatures(self, image_data: bytes) -> List[Dict[str, Any]]:
        """
        检测图像中的多个签名
        
        Args:
            image_data: 图像字节数据
            
        Returns:
            签名列表
        """
        try:
            traditional_result = self._traditional_signature_detection(image_data)
            signatures = []
            
            for region in traditional_result.get('regions', []):
                if region['confidence'] > 0.2:  # 更低的阈值用于多签名检测
                    signatures.append({
                        'bbox': region['bbox'],
                        'confidence': region['confidence'],
                        'type': 'handwritten_signature',
                        'area': region['area']
                    })
            
            # 使用NMS去除重叠的检测框
            signatures = self._non_max_suppression(signatures)
            
            return signatures
            
        except Exception as e:
            logger.error(f"多签名检测失败: {e}")
            return []
    
    def _non_max_suppression(self, signatures: List[Dict[str, Any]], overlap_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        非极大值抑制，去除重叠的检测框
        
        Args:
            signatures: 签名检测结果列表
            overlap_threshold: 重叠阈值
            
        Returns:
            过滤后的签名列表
        """
        if not signatures:
            return []
        
        # 按置信度排序
        signatures.sort(key=lambda x: x['confidence'], reverse=True)
        
        filtered_signatures = []
        
        for current in signatures:
            is_duplicate = False
            current_bbox = current['bbox']
            
            for existing in filtered_signatures:
                existing_bbox = existing['bbox']
                
                # 计算IoU
                iou = self._calculate_iou(current_bbox, existing_bbox)
                
                if iou > overlap_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_signatures.append(current)
        
        return filtered_signatures
    
    def _calculate_iou(self, bbox1: Tuple[int, int, int, int], bbox2: Tuple[int, int, int, int]) -> float:
        """
        计算两个边界框的IoU
        
        Args:
            bbox1: 第一个边界框 (x, y, w, h)
            bbox2: 第二个边界框 (x, y, w, h)
            
        Returns:
            IoU值
        """
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # 转换为 (x1, y1, x2, y2) 格式
        box1 = (x1, y1, x1 + w1, y1 + h1)
        box2 = (x2, y2, x2 + w2, y2 + h2)
        
        # 计算交集
        inter_x1 = max(box1[0], box2[0])
        inter_y1 = max(box1[1], box2[1])
        inter_x2 = min(box1[2], box2[2])
        inter_y2 = min(box1[3], box2[3])
        
        if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
            return 0.0
        
        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        
        # 计算并集
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area 