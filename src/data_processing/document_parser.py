import os
import docx
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Any, Tuple
import cv2
import numpy as np
from paddleocr import PaddleOCR
import logging

logger = logging.getLogger(__name__)

class DocumentParser:
    """文档解析器，支持DOCX和PDF格式"""
    
    def __init__(self, ocr_engine="paddleocr"):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        
    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """解析文档，返回文本和图像内容"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        if file_path.suffix.lower() == '.docx':
            return self._parse_docx(file_path)
        elif file_path.suffix.lower() == '.pdf':
            return self._parse_pdf(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")
    
    def _parse_docx(self, file_path: Path) -> Dict[str, Any]:
        """解析DOCX文件"""
        doc = docx.Document(file_path)
        
        # 提取文本内容
        text_content = []
        tables = []
        images = []
        
        # 解析段落
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append({
                    'type': 'paragraph',
                    'content': paragraph.text.strip(),
                    'style': paragraph.style.name if paragraph.style else None
                })
        
        # 解析表格
        for table_idx, table in enumerate(doc.tables):
            table_data = []
            for row in table.rows:
                row_data = []
                for cell in row.cells:
                    row_data.append(cell.text.strip())
                table_data.append(row_data)
            tables.append({
                'index': table_idx,
                'data': table_data
            })
        
        # 解析图片（从文档关系中提取）
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                try:
                    image_data = rel.target_part.blob
                    images.append({
                        'data': image_data,
                        'filename': rel.target_ref.split('/')[-1]
                    })
                except Exception as e:
                    logger.warning(f"无法提取图片: {e}")
        
        return {
            'text_content': text_content,
            'tables': tables,
            'images': images,
            'total_pages': len(doc.sections),
            'file_type': 'docx'
        }
    
    def _parse_pdf(self, file_path: Path) -> Dict[str, Any]:
        """解析PDF文件"""
        doc = fitz.open(file_path)
        
        text_content = []
        tables = []
        images = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            # 提取文本
            text = page.get_text()
            if text.strip():
                text_content.append({
                    'type': 'page',
                    'page_number': page_num + 1,
                    'content': text.strip()
                })
            
            # 提取图片
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n < 5:  # 非CMYK图像
                        img_data = pix.tobytes("png")
                        images.append({
                            'page_number': page_num + 1,
                            'image_index': img_index,
                            'data': img_data,
                            'filename': f"page_{page_num+1}_img_{img_index}.png"
                        })
                    pix = None
                except Exception as e:
                    logger.warning(f"无法提取第{page_num+1}页图片{img_index}: {e}")
        
        doc.close()
        
        return {
            'text_content': text_content,
            'tables': tables,
            'images': images,
            'total_pages': len(doc),
            'file_type': 'pdf'
        }
    
    def extract_text_from_image(self, image_data: bytes) -> str:
        """从图片中提取文字"""
        try:
            # 将字节数据转换为numpy数组
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # 使用OCR提取文字
            result = self.ocr.ocr(img, cls=True)
            
            text_list = []
            for line in result:
                if line:
                    for word_info in line:
                        text_list.append(word_info[1][0])
            
            return ' '.join(text_list)
        except Exception as e:
            logger.error(f"图片文字识别失败: {e}")
            return ""