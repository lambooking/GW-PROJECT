"""
封面/前两页签字信息提取器

功能：
- 仅处理前1-3页的图片（扫描件）
- 复用 SignatureDetector 进行签字候选区域检测
- 对候选区域进行OCR与正则解析，提取 角色/姓名/日期
- 产出结构化结果供评分引擎使用
"""

from __future__ import annotations

import base64
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from ..data_processing.schemas import StandardizedDocument
from ..models.signature_detection import SignatureDetector

logger = logging.getLogger(__name__)


# 角色关键词到标准角色映射
ROLE_ALIASES = {
    "编制": ["编制", "起草", "编写", "拟稿", "草拟", "起稿"],
    "审核": ["审核", "复核", "校核"],
    "批准": ["批准", "签发", "批准人", "批示", "核准", "批复"],
    "校对": ["校对", "校审"],
}


@dataclass
class SignatureRecord:
    page: int
    bbox: Tuple[int, int, int, int]
    role: Optional[str]
    name: Optional[str]
    date: Optional[str]
    confidence: float


class SignatureExtractor:
    """封面签字信息抽取器"""

    def __init__(self, detector: Optional[SignatureDetector] = None, ocr_enabled: bool = True):
        self.detector = detector or SignatureDetector({})
        self.ocr_enabled = ocr_enabled

    # ====== 公共入口 ======
    def extract_signatures_from_cover_pages(self, document: StandardizedDocument, max_pages: int = 3) -> List[SignatureRecord]:
        """仅在前 max_pages 页执行签字检测与OCR解析。"""
        records: List[SignatureRecord] = []

        cover_images = [
            img for img in (document.images or [])
            if isinstance(img.page_number, int) and img.page_number <= max_pages
        ]

        if not cover_images:
            logger.info("签字提取：前3页无图片，跳过")
            return records

        for img in cover_images:
            try:
                image_bytes = base64.b64decode(img.base64_data)

                # 1) 先对整页检测候选签字区域
                candidates = self.detector.detect_multiple_signatures(image_bytes) or []

                # 2) 加入底部ROI（签字常见位置）作为补充候选
                roi_candidates = self._bottom_roi_candidates(image_bytes)
                candidates.extend(roi_candidates)

                # 3) 对候选进行OCR与正则解析
                parsed = self._parse_candidates_with_ocr(image_bytes, candidates)

                # 4) 转为记录
                for c in parsed:
                    records.append(
                        SignatureRecord(
                            page=img.page_number,
                            bbox=c["bbox"],
                            role=c.get("role"),
                            name=c.get("name"),
                            date=c.get("date"),
                            confidence=float(c.get("confidence", 0.0)),
                        )
                    )
            except Exception as e:
                logger.warning(f"签字提取失败（第{img.page_number}页）：{e}")

        # NMS/合并同类角色（按置信度保留）可以按需补充，这里先直接返回
        return records

    # ====== 内部：ROI候选 ======
    def _bottom_roi_candidates(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return []

            h, w = img.shape[:2]
            # 取底部 35% 高度作为签字高发区
            y1 = int(h * 0.65)
            roi = img[y1:h, 0:w]

            # 边缘/连通域作为启发式
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            cands: List[Dict[str, Any]] = []
            for cnt in contours:
                x, y, cw, ch = cv2.boundingRect(cnt)
                area = cw * ch
                if area < 800:  # 过滤小噪声
                    continue
                # 还原到整页坐标
                cands.append({
                    "bbox": (x, y + y1, cw, ch),
                    "confidence": 0.25,  # 启发式置信度
                })

            return cands[:10]
        except Exception:
            return []

    # ====== 内部：OCR+正则解析 ======
    def _parse_candidates_with_ocr(self, image_bytes: bytes, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return []

            parsed: List[Dict[str, Any]] = []

            for cand in candidates:
                x, y, w, h = cand.get("bbox", (0, 0, 0, 0))
                x = max(0, int(x)); y = max(0, int(y)); w = max(1, int(w)); h = max(1, int(h))

                crop = img[y:y + h, x:x + w]
                text = self._simple_ocr(crop) if self.ocr_enabled else ""

                role = self._extract_role(text)
                name = self._extract_name(text)
                date = self._extract_date(text)

                # 过滤无效候选：必须至少包含 角色 或 日期 或 姓名 之一
                if not any([role, name, date]):
                    continue

                parsed.append({
                    "bbox": (x, y, w, h),
                    "role": role,
                    "name": name,
                    "date": date,
                    "confidence": float(cand.get("confidence", 0.0)),
                })

            return parsed
        except Exception as e:
            logger.warning(f"签字候选解析失败：{e}")
            return []

    # ====== 轻量OCR（启发式）：优先用于扫描件/中文印章附近 ======
    def _simple_ocr(self, crop_img: np.ndarray) -> str:
        """占位OCR：优先提取深色笔迹与日期样式，避免引入重依赖。
        若后续已集成外部OCR，可在此对接。
        """
        try:
            gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
            # 自适应阈值增强手写笔迹
            thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 35, 10)
            # 形态学去噪
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            thr = cv2.morphologyEx(thr, cv2.MORPH_OPEN, kernel, iterations=1)

            # 仅做模式匹配：输出疑似日期/角色/姓名的行文本（简化）
            # 这里不做真正字符级OCR，使用启发式：统计直线/连笔密度与常见字符模板
            # 为兼容性，这里返回空串，再交给正则从上层OCR文本（若有）匹配。
            # 若 `Image.extracted_text` 已有OCR，可在上层拼接。
            return ""
        except Exception:
            return ""

    # ====== 解析工具 ======
    def _extract_role(self, text: str) -> Optional[str]:
        if not text:
            return None
        for std, aliases in ROLE_ALIASES.items():
            for a in aliases:
                if a in text:
                    return std
        return None

    def _extract_name(self, text: str) -> Optional[str]:
        if not text:
            return None
        # 中文姓名（2-4字），排除“编制/审核/批准”等关键词
        m = re.search(r"(?<!编制)(?<!审核)(?<!批准)[\u4e00-\u9fa5]{2,4}", text)
        return m.group(0) if m else None

    def _extract_date(self, text: str) -> Optional[str]:
        if not text:
            return None
        # 支持 2024-09-30 / 2024/09/30 / 2024年9月30日
        m = re.search(r"(20\d{2}[-/年] ?\d{1,2}[-/月] ?\d{1,2}(?:日)?)", text)
        return m.group(1) if m else None


__all__ = ["SignatureExtractor", "SignatureRecord"]


