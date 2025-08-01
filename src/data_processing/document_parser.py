import docx
from pathlib import Path
from typing import Dict, Any
import cv2
import numpy as np
from paddleocr import PaddleOCR
import logging

logger = logging.getLogger(__name__)

class DocumentParser:
    """
    一个专注于解析DOCX文件的组件。
    它提取文本、表格和图片，并提供OCR功能。
    PDF的解析已移至EnhancedPDFParser。
    """
    
    def __init__(self):
        """
        初始化解析器和OCR引擎。
        """
        try:
            self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        except Exception as e:
            logger.error(f"PaddleOCR 初始化失败，请检查环境配置: {e}")
            self.ocr = None

    def parse_docx(self, file_path: Path) -> Dict[str, Any]:
        """
        解析DOCX文件，提取文本、表格和图片。

        Args:
            file_path: 指向DOCX文件的路径对象。

        Returns:
            一个包含原始解析数据的字典。
        """
        doc = docx.Document(file_path)
        
        text_content = []
        tables = []
        images = []
        
        # 解析段落
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append({
                    'type': 'paragraph',
                    'content': paragraph.text.strip(),
                    'style': paragraph.style.name if paragraph.style else 'Normal'
                })
        
        # 解析表格
        for table_idx, table in enumerate(doc.tables):
            table_data = []
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                table_data.append(row_data)
            tables.append({
                'index': table_idx,
                'data': table_data
            })
        
        # 解析图片（从文档关系中提取）
        image_rels = [
            rel for rel in doc.part.rels.values()
            if "image" in rel.target_ref
        ]
        
        for rel in image_rels:
            try:
                image_data = rel.target_part.blob
                images.append({
                    'data': image_data,
                    'filename': rel.target_ref.split('/')[-1]
                })
            except Exception as e:
                logger.warning(f"无法提取图片 '{rel.target_ref}': {e}")
        
        # 计算页数（这是一个估算值，python-docx不直接提供页数）
        total_pages = 0
        try:
            total_pages = doc.core_properties.pages
        except AttributeError:
             # 对于没有页数属性的旧文档，可以基于内容估算
             total_pages = max(1, round(len(doc.paragraphs) / 50) + len(doc.tables))
             logger.warning("无法获取精确页数，使用估算值。")


        return {
            'text_content': text_content,
            'tables': tables,
            'images': images,
            'total_pages': total_pages,
            'file_type': 'docx'
        }

    def extract_text_from_image(self, image_data: bytes) -> str:
        """
        使用OCR从图片的二进制数据中提取文字。

        Args:
            image_data: 图片的字节数据。

        Returns:
            提取出的文字字符串，如果识别失败则返回空字符串。
        """
        if not self.ocr:
            logger.error("OCR引擎未初始化，无法提取图片文字。")
            return ""
            
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("无法解码图片数据")

            result = self.ocr.ocr(img, cls=True)
            
            text_list = []
            if result:
                for res_block in result:
                    if res_block:
                        for line in res_block:
                            text_list.append(line[1][0])
            
            return ' '.join(text_list)
        except Exception as e:
            logger.error(f"图片文字识别失败: {e}", exc_info=True)
            return ""
