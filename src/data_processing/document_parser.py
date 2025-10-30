import docx
from pathlib import Path
from typing import Dict, Any
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class DocumentParser:
    """
    一个专注于解析DOCX文件的组件。
    它提取文本、表格和图片，并提供OCR功能。
    PDF的解析已移至EnhancedPDFParser。
    """
    
    def __init__(self, enable_ocr: bool = False):
        """
        初始化解析器和可选的OCR引擎。
        """
        self.ocr = None
        if enable_ocr:
            try:
                # 延迟导入，避免在不需要时加载OCR依赖与模型
                from paddleocr import PaddleOCR  # type: ignore
                self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
            except Exception as e:
                logger.error(f"PaddleOCR 初始化失败，已禁用OCR: {e}")
                self.ocr = None

    def parse_docx(self, file_path: Path, max_images: int = None) -> Dict[str, Any]:
        """
        解析DOCX文件，提取文本、表格和图片。

        Args:
            file_path: 指向DOCX文件的路径对象。
            max_images: 可选，最多提取的图片数量。None表示提取所有图片。
                       用于优化：如签字页只需前3张图片，设置max_images=3可大幅提升性能。

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
        
        # 改进的图片提取：按文档流顺序遍历所有元素
        # 这样可以确保图片顺序与文档中的实际出现顺序一致
        image_counter = 0
        seen_image_ids = set()  # 用于去重
        
        # 日志提示
        if max_images is not None:
            logger.info(f"DOCX图片提取：启用限制模式，最多提取前 {max_images} 张图片（用于签字页优化）")
        
        # 遍历文档中的所有元素（段落和表格按文档顺序混合）
        early_stop = False  # 标记是否提前停止
        for element in doc.element.body:
            if early_stop:
                break
            # 检查段落中的图片
            if element.tag.endswith('p'):  # 段落
                for run in element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):
                    # 兼容 inline 与 anchor 两种嵌入方式
                    for drawing in run.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline') + \
                                   run.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}anchor'):
                        # 提取图片关系ID（a:blip）
                        blip = drawing.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
                        if blip is None:
                            # 部分文档结构为 pic:pic/pic:blipFill/a:blip
                            blip = drawing.find('.//{http://schemas.openxmlformats.org/drawingml/2006/picture}blipFill/')
                        if blip is None:
                            blip = drawing.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
                        if blip is not None:
                            embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                            if embed_id and embed_id not in seen_image_ids:
                                try:
                                    image_part = doc.part.related_parts[embed_id]
                                    image_data = image_part.blob
                                    image_counter += 1
                                    images.append({
                                        'data': image_data,
                                        'filename': image_part.partname.split('/')[-1],
                                        'page_number': image_counter,  # 按文档流顺序分配页码
                                        'embed_id': embed_id
                                    })
                                    seen_image_ids.add(embed_id)
                                    logger.debug(f"提取图片 {image_counter}: {embed_id}")
                                    
                                    # 检查是否达到图片数量限制
                                    if max_images is not None and image_counter >= max_images:
                                        logger.info(f"已达到图片提取限制 ({max_images} 张)，停止提取")
                                        early_stop = True
                                        break
                                        
                                except Exception as e:
                                    logger.warning(f"提取图片 {embed_id} 失败: {e}")
            
            # 检查表格单元格中的图片
            elif element.tag.endswith('tbl'):  # 表格
                for cell in element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc'):
                    for run in cell.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r'):
                        for drawing in run.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline') + \
                                       run.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}anchor'):
                            blip = drawing.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
                            if blip is None:
                                blip = drawing.find('.//{http://schemas.openxmlformats.org/drawingml/2006/picture}blipFill/')
                            if blip is None:
                                blip = drawing.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
                            if blip is not None:
                                embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                                if embed_id and embed_id not in seen_image_ids:
                                    try:
                                        image_part = doc.part.related_parts[embed_id]
                                        image_data = image_part.blob
                                        image_counter += 1
                                        images.append({
                                            'data': image_data,
                                            'filename': image_part.partname.split('/')[-1],
                                            'page_number': image_counter,
                                            'embed_id': embed_id
                                        })
                                        seen_image_ids.add(embed_id)
                                        logger.debug(f"提取表格中的图片 {image_counter}: {embed_id}")
                                        
                                        # 检查是否达到图片数量限制
                                        if max_images is not None and image_counter >= max_images:
                                            logger.info(f"已达到图片提取限制 ({max_images} 张)，停止提取")
                                            early_stop = True
                                            break
                                            
                                    except Exception as e:
                                        logger.warning(f"提取表格图片 {embed_id} 失败: {e}")
                            
                            if early_stop:
                                break
                    if early_stop:
                        break
        
        logger.info(f"DOCX图片提取完成：共 {image_counter} 张图片，按文档顺序排列")

        # —— 为每张图片计算宽高并推断是否为整页扫描（便于后续签字页优先）
        # 规则：
        # 1) min(width,height) >= 1000 像素（清晰大图）
        # 2) 纵横比接近A4竖版（w/h≈0.707，容差±0.15）
        # 3) 或者面积为文档Top-2
        try:
            dims = []
            for item in images:
                data = item.get('data')
                if not data:
                    dims.append((0, 0, 0))
                    continue
                np_arr = np.frombuffer(data, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if img is None:
                    dims.append((0, 0, 0))
                    continue
                h, w = img.shape[:2]
                area = int(w) * int(h)
                item['width_px'] = int(w)
                item['height_px'] = int(h)
                item['size_bytes'] = len(data)
                dims.append((w, h, area))

            # 依据面积排序，选取Top-2作为整页候选
            areas = [a for (_, _, a) in dims]
            top_areas = sorted(areas, reverse=True)[:2]

            for idx, item in enumerate(images):
                w, h, area = dims[idx]
                is_full = False
                if w > 0 and h > 0:
                    ratio = (w / float(h)) if h else 0.0
                    big_enough = min(w, h) >= 1000
                    ratio_ok = abs(ratio - 0.707) <= 0.15 or abs((h / float(max(1, w))) - 0.707) <= 0.15
                    top_area = area in top_areas
                    if big_enough and ratio_ok:
                        is_full = True
                    elif top_area:
                        is_full = True
                item['is_full_page'] = bool(is_full)
        except Exception as e:
            logger.warning(f"DOCX图片尺寸与整页判断失败: {e}")
        
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

            # 兼容不同PaddleOCR版本：实例已配置use_angle_cls，无需在调用时传cls参数
            try:
                result = self.ocr.ocr(img)
            except TypeError:
                # 少数旧版需要不带关键字的调用
                result = self.ocr.ocr(img)
            
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
