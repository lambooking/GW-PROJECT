"""
智能图片选择器
根据评分项的具体要求，精准选择最相关的图片发送给AI模型
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
import base64
import cv2
import numpy as np

from ..data_processing.schemas import StandardizedDocument, Image

logger = logging.getLogger(__name__)


class SmartImageSelector:
    """智能图片选择器 - 根据评分项要求精准选择图片"""
    
    def __init__(self):
        """初始化图片选择器"""
        pass
    
    def select_images_for_criterion(
        self,
        document: StandardizedDocument,
        criterion_key: str,
        criterion_config: Dict[str, Any],
        limit: int = 3
    ) -> List[str]:
        """
        为特定评分项选择最相关的图片
        
        Args:
            document: 标准化文档
            criterion_key: 评分项键名
            criterion_config: 评分项配置
            limit: 最多选择的图片数量（多模态问题会自动调整为至少3张）
            
        Returns:
            选中的图片base64列表
        """
        all_images = list(document.images or [])
        
        if not all_images:
            logger.warning(f"文档中无图片")
            return []
        
        # 根据评分项类型选择不同的策略
        criterion_type = criterion_config.get("type", "")
        evaluation_focus = criterion_config.get("evaluation_focus", "")
        image_keywords = criterion_config.get("image_keywords", [])
        check_items = criterion_config.get("check_items", [])
        
        # 智能判断是否为多模态问题，自动调整图片数量
        is_multimodal = self._is_multimodal_criterion(criterion_type, criterion_config)
        if is_multimodal and limit < 3:
            original_limit = limit
            limit = 3
            logger.info(f"检测到多模态评分项，将图片数量从 {original_limit} 调整为 {limit}")
        
        logger.info(f"为评分项 '{criterion_config.get('name', criterion_key)}' 选择图片")
        logger.info(f"  类型: {criterion_type}, 多模态: {is_multimodal}, 评估重点: {evaluation_focus}")
        logger.info(f"  图片限制: {limit}, 关键词: {image_keywords}")
        
        # 根据评分项选择策略
        if criterion_key == "signature_recognition" or "signature" in criterion_key.lower():
            return self._select_signature_images(all_images, limit, criterion_config)
        elif criterion_key == "evacuation_route_annotation" or "evacuation" in criterion_key.lower() or "疏散" in evaluation_focus:
            return self._select_evacuation_route_images(all_images, limit, criterion_config)
        elif criterion_key == "entry_route_annotation" or "入场" in evaluation_focus:
            return self._select_entry_route_images(all_images, limit, criterion_config)
        elif criterion_key == "image_annotation_recognition" or "影像图" in evaluation_focus:
            return self._select_image_annotation_images(all_images, limit, criterion_config)
        elif criterion_key == "image_text_consistency" or "标注一致性" in evaluation_focus:
            return self._select_consistency_check_images(all_images, limit, criterion_config)
        elif criterion_key == "hca_coverage" or "高后果区" in evaluation_focus:
            return self._select_hca_images(all_images, limit, criterion_config)
        else:
            # 通用选择策略
            return self._select_by_keywords(all_images, image_keywords, limit, criterion_config)
    
    def _select_signature_images(
        self,
        images: List[Image],
        limit: int,
        config: Dict[str, Any]
    ) -> List[str]:
        """
        选择签字页图片 - 针对比赛评分优化
        
        策略：
        - 优先选择前3页（签字页通常在文档开头）
        - 每页最多2张，确保覆盖不同签字区域
        - 提高红色印章、表格线的权重
        - 至少选择3张图片（如果可用）
        """
        pages = config.get("pages", [1, 2, 3])
        max_page = max(pages) if pages else 3
        
        # 确保至少选择3张签字图片
        effective_limit = max(limit, 3)
        
        scored_images = []
        
        for img in images:
            if not img.base64_data:
                continue
            
            score = 0.0
            page = getattr(img, 'page_number', 99) or 99
            
            # 1. 页码优先（前3页） - 权重提升
            if isinstance(page, int) and 1 <= page <= max_page:
                # 第1页优先级最高
                if page == 1:
                    score += 2000.0
                elif page == 2:
                    score += 1500.0
                elif page == 3:
                    score += 1200.0
                else:
                    score += 1000.0
            elif page <= max_page * 2:  # 放宽到前6页
                score += 300.0
            
            # 2. OCR文本关键词匹配 - 增强匹配
            ocr_text = (img.extracted_text or "").lower()
            signature_keywords = [
                "编制", "审核", "批准", "校对", "签字", "签章", 
                "盖章", "评审意见", "签发", "签名", "确认"
            ]
            keyword_hits = sum(1 for kw in signature_keywords if kw in ocr_text)
            score += keyword_hits * 150.0  # 从100提升到150
            
            # 3. 日期模式匹配 - 增强权重
            date_patterns = [
                r"\d{4}年\d{1,2}月\d{1,2}日",
                r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
                r"\d{4}\.\d{1,2}\.\d{1,2}"
            ]
            for pattern in date_patterns:
                if re.search(pattern, ocr_text):
                    score += 100.0  # 从50提升到100
                    break
            
            # 4. 视觉特征（红色印章、表格线） - 权重大幅提升
            visual_score = self._estimate_signature_visual_relevance(img.base64_data)
            score += visual_score * 500.0  # 从200提升到500
            
            # 5. 图片ID特征 - 全页图片优先
            image_id = getattr(img, 'image_id', '')
            if '_full' in image_id or 'page_' in image_id:
                score += 200.0  # 从100提升到200
            
            # 6. 表格特征检测（签字页通常有表格）
            if self._has_table_structure(img.base64_data):
                score += 300.0
            
            scored_images.append((score, img, page))
        
        # 排序并选择
        scored_images.sort(key=lambda x: x[0], reverse=True)
        
        # 每页最多2张，确保覆盖前3页
        selected = []
        page_count = {}
        pages_covered = set()
        
        # 第一轮：优先确保前3页都有覆盖
        for score, img, page in scored_images:
            if len(pages_covered) >= 3:
                break
            if page <= 3 and page not in pages_covered:
                selected.append(img.base64_data)
                page_count[page] = 1
                pages_covered.add(page)
                logger.debug(f"选择签字图片（优先覆盖）: 第{page}页, 分数={score:.1f}")
        
        # 第二轮：填充到目标数量
        for score, img, page in scored_images:
            if len(selected) >= effective_limit:
                break
            count = page_count.get(page, 0)
            # 每页最多2张
            if count < 2:
                # 避免重复
                if img.base64_data not in selected:
                    selected.append(img.base64_data)
                    page_count[page] = count + 1
                    logger.debug(f"选择签字图片（补充）: 第{page}页, 分数={score:.1f}")
        
        logger.info(f"签字图片选择完成: 从{len(images)}张中选择{len(selected)}张，覆盖页码: {sorted(pages_covered)}")
        return selected
    
    def _select_evacuation_route_images(
        self,
        images: List[Image],
        limit: int,
        config: Dict[str, Any]
    ) -> List[str]:
        """选择应急疏散路线图图片 - 重点选择有路线标注的地图类图片"""
        scored_images = []
        
        for img in images:
            if not img.base64_data:
                continue
            
            score = 0.0
            ocr_text = (img.extracted_text or "").lower()
            
            # 1. 必须包含的关键词（高优先级）
            required_keywords = ["疏散", "逃生", "集合点", "集结点", "应急"]
            has_required = any(kw in ocr_text for kw in required_keywords)
            if not has_required:
                # 如果完全没有关键词，跳过（除非是地图类图片）
                if not self._is_map_like_image(img.base64_data):
                    continue
            
            # 2. 路线相关关键词
            route_keywords = ["路线", "路径", "通道", "方向", "箭头", "标注"]
            route_hits = sum(1 for kw in route_keywords if kw in ocr_text)
            score += route_hits * 150.0
            
            # 3. 集合点相关关键词
            assembly_keywords = ["集合点", "集结点", "疏散点", "安全区", "位置"]
            assembly_hits = sum(1 for kw in assembly_keywords if kw in ocr_text)
            score += assembly_hits * 200.0
            
            # 4. 疏散方向相关
            direction_keywords = ["两侧", "方向", "箭头", "指示", "指向"]
            direction_hits = sum(1 for kw in direction_keywords if kw in ocr_text)
            score += direction_hits * 100.0
            
            # 5. 影响半径相关
            if "影响半径" in ocr_text or "半径" in ocr_text:
                score += 150.0
            
            # 6. 视觉特征：地图类图片优先
            if self._is_map_like_image(img.base64_data):
                score += 500.0
                # 检查是否有路线标记（通过线条检测）
                if self._has_route_lines(img.base64_data):
                    score += 300.0
                # 检查是否有标注文字
                if self._has_text_annotations(img.base64_data):
                    score += 200.0
            
            # 7. 排除明显不相关的图片
            if self._is_blank_or_text_only(img.base64_data, ocr_text):
                score -= 1000.0  # 大幅降低分数
            
            # 8. 页码信息（前几页的相关图片可能更准确）
            page = getattr(img, 'page_number', 99) or 99
            if isinstance(page, int) and page <= 10:
                score += 50.0 / page  # 页码越小越优先
            
            scored_images.append((score, img))
        
        # 排序并选择
        scored_images.sort(key=lambda x: x[0], reverse=True)
        selected = [img.base64_data for score, img in scored_images[:limit] if score > 0]
        
        logger.info(f"应急疏散路线图片选择: 从{len(images)}张中选择{len(selected)}张")
        if selected:
            for i, (score, img) in enumerate(scored_images[:len(selected)]):
                ocr_preview = (img.extracted_text or "")[:60].replace("\n", " ")
                logger.debug(f"  选中图{i+1}: 分数={score:.1f}, OCR预览={ocr_preview}...")
        
        return selected
    
    def _select_entry_route_images(
        self,
        images: List[Image],
        limit: int,
        config: Dict[str, Any]
    ) -> List[str]:
        """选择入场线路图图片"""
        scored_images = []
        
        for img in images:
            if not img.base64_data:
                continue
            
            score = 0.0
            ocr_text = (img.extracted_text or "").lower()
            
            # 1. 入场相关关键词
            entry_keywords = ["入场", "进入", "路线", "路径", "道路"]
            entry_hits = sum(1 for kw in entry_keywords if kw in ocr_text)
            score += entry_hits * 150.0
            
            # 2. 标注相关
            if "标注" in ocr_text or "说明" in ocr_text:
                score += 100.0
            
            # 3. 合理性检查相关（穿山、穿墙等限制）
            constraint_keywords = ["合理", "可行", "道路", "桥", "障碍"]
            constraint_hits = sum(1 for kw in constraint_keywords if kw in ocr_text)
            score += constraint_hits * 80.0
            
            # 4. 地图类图片优先
            if self._is_map_like_image(img.base64_data):
                score += 500.0
                if self._has_route_lines(img.base64_data):
                    score += 300.0
            
            # 5. 排除空白页
            if self._is_blank_or_text_only(img.base64_data, ocr_text):
                score -= 1000.0
            
            scored_images.append((score, img))
        
        scored_images.sort(key=lambda x: x[0], reverse=True)
        selected = [img.base64_data for score, img in scored_images[:limit] if score > 0]
        
        logger.info(f"入场线路图片选择: 从{len(images)}张中选择{len(selected)}张")
        return selected
    
    def _select_image_annotation_images(
        self,
        images: List[Image],
        limit: int,
        config: Dict[str, Any]
    ) -> List[str]:
        """选择影像图标注识别相关图片"""
        scored_images = []
        
        for img in images:
            if not img.base64_data:
                continue
            
            score = 0.0
            ocr_text = (img.extracted_text or "").lower()
            
            # 1. 影像图相关关键词
            image_keywords = ["影像图", "影像", "图像", "卫星", "航拍", "示意图"]
            image_hits = sum(1 for kw in image_keywords if kw in ocr_text)
            score += image_hits * 200.0
            
            # 2. 管道位置相关
            if "管道" in ocr_text and ("位置" in ocr_text or "标注" in ocr_text):
                score += 300.0
            
            # 3. 影响半径相关
            if "影响半径" in ocr_text or ("潜在" in ocr_text and "半径" in ocr_text):
                score += 250.0
            
            # 4. 实线虚线相关
            if "实线" in ocr_text or "虚线" in ocr_text or "线条" in ocr_text:
                score += 200.0
            
            # 5. 建筑物标注相关
            building_keywords = ["建筑物", "建筑", "名称", "人员数量", "环境受体"]
            building_hits = sum(1 for kw in building_keywords if kw in ocr_text)
            score += building_hits * 150.0
            
            # 6. 视觉特征：地图/影像类图片
            if self._is_map_like_image(img.base64_data):
                score += 400.0
                if self._has_text_annotations(img.base64_data):
                    score += 300.0
            
            scored_images.append((score, img))
        
        scored_images.sort(key=lambda x: x[0], reverse=True)
        selected = [img.base64_data for score, img in scored_images[:limit] if score > 0]
        
        logger.info(f"影像图标注图片选择: 从{len(images)}张中选择{len(selected)}张")
        return selected
    
    def _select_hca_images(
        self,
        images: List[Image],
        limit: int,
        config: Dict[str, Any]
    ) -> List[str]:
        """选择高后果区相关图片"""
        scored_images = []
        
        for img in images:
            if not img.base64_data:
                continue
            
            score = 0.0
            ocr_text = (img.extracted_text or "").lower()
            
            # 1. 高后果区关键词
            hca_keywords = ["高后果区", "hca", "后果区", "风险区"]
            hca_hits = sum(1 for kw in hca_keywords if kw in ocr_text)
            score += hca_hits * 300.0
            
            # 2. 影像图相关
            if "影像图" in ocr_text or "影像" in ocr_text:
                score += 200.0
            
            # 3. 现场图相关
            if "现场图" in ocr_text or "现场" in ocr_text:
                score += 150.0
            
            # 4. 地图类图片
            if self._is_map_like_image(img.base64_data):
                score += 400.0
            
            scored_images.append((score, img))
        
        scored_images.sort(key=lambda x: x[0], reverse=True)
        selected = [img.base64_data for score, img in scored_images[:limit] if score > 0]
        
        logger.info(f"高后果区图片选择: 从{len(images)}张中选择{len(selected)}张")
        return selected
    
    def _select_consistency_check_images(
        self,
        images: List[Image],
        limit: int,
        config: Dict[str, Any]
    ) -> List[str]:
        """选择用于一致性检查的图片（需要与文本描述对比）"""
        # 一致性检查需要同时选择图片和对应的文本描述区域
        # 优先选择有标注的影像图
        return self._select_image_annotation_images(images, limit, config)
    
    def _select_by_keywords(
        self,
        images: List[Image],
        keywords: List[str],
        limit: int,
        config: Dict[str, Any]
    ) -> List[str]:
        """基于关键词的通用选择策略"""
        scored_images = []
        normalized_keywords = [k.lower() for k in keywords]
        
        for img in images:
            if not img.base64_data:
                continue
            
            score = 0.0
            ocr_text = (img.extracted_text or "").lower()
            
            # 关键词匹配
            hits = sum(1 for kw in normalized_keywords if kw in ocr_text)
            score += hits * 100.0
            
            # 排除空白页
            if self._is_blank_or_text_only(img.base64_data, ocr_text):
                score -= 500.0
            
            scored_images.append((score, img))
        
        scored_images.sort(key=lambda x: x[0], reverse=True)
        selected = [img.base64_data for score, img in scored_images[:limit] if score > 0]
        
        logger.info(f"关键词选择图片: 从{len(images)}张中选择{len(selected)}张")
        return selected
    
    def _is_multimodal_criterion(self, criterion_type: str, criterion_config: Dict[str, Any]) -> bool:
        """
        判断评分项是否为多模态问题（需要图片）
        
        Args:
            criterion_type: 评分项类型
            criterion_config: 评分项配置
            
        Returns:
            是否为多模态问题
        """
        # 1. 通过 type 字段判断
        if criterion_type:
            multimodal_types = [
                "multimodal_signature",  # 签字识别
                "multimodal_image",      # 影像图标注
                "multimodal_route",      # 入场/逃生路线图
                "multimodal_evacuation", # 疏散路线图
                "multimodal_hca",        # 高后果区影像
                "multimodal_risk",       # 风险标识
                "multimodal_evac"        # 应急疏散
            ]
            if criterion_type in multimodal_types:
                return True
        
        # 2. 通过 image_keywords 字段判断
        image_keywords = criterion_config.get("image_keywords", [])
        if image_keywords and len(image_keywords) > 0:
            return True
        
        # 3. 通过评分项名称判断
        name = criterion_config.get("name", "")
        multimodal_keywords = [
            "签字", "图片", "影像", "图标注", "路线图", 
            "现场图", "示意图", "标识", "标注"
        ]
        if any(kw in name for kw in multimodal_keywords):
            return True
        
        # 4. 通过 evaluation_focus 判断
        focus = criterion_config.get("evaluation_focus", "")
        if "图片" in focus or "识别" in focus or "标注" in focus:
            return True
        
        return False
    
    # ========== 辅助方法：图片特征检测 ==========
    
    def _is_map_like_image(self, image_base64: str) -> bool:
        """判断是否为地图类图片"""
        try:
            if image_base64.startswith("data:image"):
                b64 = image_base64.split(",", 1)[-1]
            else:
                b64 = image_base64
            
            img_bytes = base64.b64decode(b64)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if img is None:
                return False
            
            h, w = img.shape[:2]
            if h == 0 or w == 0:
                return False
            
            # 地图特征：
            # 1. 颜色多样性（地图通常有多种颜色）
            # 2. 有线条（道路、边界）
            # 3. 有文字标注区域
            
            # 颜色多样性
            unique_colors = len(np.unique(img.reshape(-1, img.shape[2]), axis=0))
            color_diversity = unique_colors / (h * w)
            
            # 线条检测
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.count_nonzero(edges) / (h * w)
            
            # 判断：颜色多样性 > 0.1 且边缘密度 > 0.05 可能是地图
            is_map = color_diversity > 0.05 and edge_density > 0.03
            
            return is_map
            
        except Exception as e:
            logger.debug(f"地图检测失败: {e}")
            return False
    
    def _has_route_lines(self, image_base64: str) -> bool:
        """检测图片中是否有路线线条"""
        try:
            if image_base64.startswith("data:image"):
                b64 = image_base64.split(",", 1)[-1]
            else:
                b64 = image_base64
            
            img_bytes = base64.b64decode(b64)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if img is None:
                return False
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # 检测直线（路线）
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=30, maxLineGap=10)
            
            return lines is not None and len(lines) > 5
            
        except Exception:
            return False
    
    def _has_text_annotations(self, image_base64: str) -> bool:
        """检测图片中是否有文字标注（通过OCR已有文本判断）"""
        # 这个方法需要配合OCR结果使用
        # 暂时返回True，实际应该检查OCR文本是否丰富
        return True
    
    def _is_blank_or_text_only(self, image_base64: str, ocr_text: str) -> bool:
        """判断是否为空白页或纯文本页（无图片内容）"""
        # 如果OCR文本很少或为空，且图片主要是白色，可能是空白页
        if len(ocr_text.strip()) < 10:
            try:
                if image_base64.startswith("data:image"):
                    b64 = image_base64.split(",", 1)[-1]
                else:
                    b64 = image_base64
                
                img_bytes = base64.b64decode(b64)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if img is None:
                    return True
                
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # 检查白色占比
                white_ratio = np.count_nonzero(gray > 240) / (gray.shape[0] * gray.shape[1])
                
                # 如果白色占比 > 90%，可能是空白页
                return white_ratio > 0.9
                
            except Exception:
                return False
        
        return False
    
    def _estimate_signature_visual_relevance(self, image_base64: str) -> float:
        """
        估算图片与签字页的视觉相关性
        
        检测特征：
        - 红色印章
        - 表格线条
        - 手写笔迹
        """
        try:
            if image_base64.startswith("data:image"):
                b64 = image_base64.split(",", 1)[-1]
            else:
                b64 = image_base64
            
            img_bytes = base64.b64decode(b64)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if img is None:
                return 0.0
            
            h, w = img.shape[:2]
            if h == 0 or w == 0:
                return 0.0
            
            # 1. 红色占比（印章） - 权重最高
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower_red1 = np.array([0, 80, 80])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 80, 80])
            upper_red2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_ratio = (np.count_nonzero(mask1) + np.count_nonzero(mask2)) / float(h * w)
            
            # 2. 线条密度（表格） - 权重提升
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 80, 180)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=min(w, h) * 0.2, maxLineGap=10)
            line_count = 0 if lines is None else len(lines)
            line_density = min(1.0, line_count / 20.0)
            
            # 3. 深色笔迹检测（手写签名）
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
            dark_ratio = np.count_nonzero(binary) / float(h * w)
            # 手写签名通常占比在 0.05-0.20 之间
            handwriting_score = 1.0 if 0.05 <= dark_ratio <= 0.20 else 0.0
            
            # 综合评分 - 红色印章权重5.0，表格线条权重1.0，手写笔迹权重0.5
            score = red_ratio * 5.0 + line_density * 1.0 + handwriting_score * 0.5
            return min(1.0, score)
            
        except Exception:
            return 0.0
    
    def _has_table_structure(self, image_base64: str) -> bool:
        """
        检测图片中是否有表格结构
        
        Returns:
            是否包含表格结构
        """
        try:
            if image_base64.startswith("data:image"):
                b64 = image_base64.split(",", 1)[-1]
            else:
                b64 = image_base64
            
            img_bytes = base64.b64decode(b64)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if img is None:
                return False
            
            h, w = img.shape[:2]
            if h == 0 or w == 0:
                return False
            
            # 检测水平和垂直线条
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            # 检测水平线
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min(w//10, 40), 1))
            horizontal_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, horizontal_kernel)
            h_lines = np.count_nonzero(horizontal_lines)
            
            # 检测垂直线
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, min(h//10, 40)))
            vertical_lines = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel)
            v_lines = np.count_nonzero(vertical_lines)
            
            # 如果同时有足够的水平线和垂直线，可能是表格
            has_table = h_lines > 100 and v_lines > 100
            
            return has_table
            
        except Exception:
            return False

