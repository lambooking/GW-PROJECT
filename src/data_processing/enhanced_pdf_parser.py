"""
增强的PDF解析器 - 支持表格提取和更精细的内容分析
"""

import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from typing import Dict, List, Any, Tuple
import cv2
import numpy as np
from paddleocr import PaddleOCR
import logging
import re

logger = logging.getLogger(__name__)

class EnhancedPDFParser:
    """增强的PDF解析器，支持表格提取"""
    
    def __init__(self, ocr_engine="paddleocr"):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        
    def parse_pdf_enhanced(self, file_path: Path) -> Dict[str, Any]:
        """
        增强的PDF解析，包含表格提取
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            解析结果字典
        """
        try:
            # 使用PyMuPDF进行基础解析
            doc_mupdf = fitz.open(file_path)
            
            # 使用pdfplumber进行表格提取
            doc_plumber = pdfplumber.open(file_path)
            
            text_content = []
            tables = []
            images = []
            
            # 逐页处理
            for page_num in range(len(doc_mupdf)):
                page_mupdf = doc_mupdf.load_page(page_num)
                page_plumber = doc_plumber.pages[page_num]
                
                # 提取文本内容
                text = page_mupdf.get_text()
                if text.strip():
                    # 清理和结构化文本
                    structured_text = self._structure_text(text, page_num + 1)
                    text_content.extend(structured_text)
                
                # 提取表格
                page_tables = self._extract_tables_from_page(page_plumber, page_num + 1)
                tables.extend(page_tables)
                
                # 提取图片
                page_images = self._extract_images_from_page(page_mupdf, doc_mupdf, page_num + 1)
                images.extend(page_images)

                # 追加：为前3页渲染整页快照，确保签字页（封面/前两页）始终有图像可用于多模态/签字检测
                try:
                    if page_num < 3:  # 仅前3页
                        snap = page_mupdf.get_pixmap(dpi=144)
                        img_data = snap.tobytes("png")
                        images.append({
                            'page_number': page_num + 1,
                            'image_index': -1,
                            'data': img_data,
                            'filename': f"page_{page_num + 1}_full.png",
                            'width': snap.width,
                            'height': snap.height,
                            'size_bytes': len(img_data),
                            'is_full_page': True
                        })
                except Exception as e:
                    logger.warning(f"无法渲染第{page_num + 1}页整页快照: {e}")
            
            total_pages = len(doc_mupdf)
            doc_mupdf.close()
            doc_plumber.close()
            
            # 后处理：合并相关内容，去重等
            processed_result = self._post_process_content(text_content, tables, images)
            
            return {
                'text_content': processed_result['text_content'],
                'tables': processed_result['tables'],
                'images': processed_result['images'],
                'total_pages': total_pages,
                'file_type': 'pdf',
                'metadata': {
                    'tables_found': len(processed_result['tables']),
                    'images_found': len(processed_result['images']),
                    'structured_sections': len(processed_result['text_content'])
                }
            }
            
        except Exception as e:
            logger.error(f"增强PDF解析失败: {e}")
            raise
    
    def _structure_text(self, text: str, page_number: int) -> List[Dict[str, Any]]:
        """将文本按结构化方式组织"""
        structured_text = []
        
        # 按行分割
        lines = text.split('\n')
        current_section = []
        section_type = 'paragraph'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 识别章节标题
            if self._is_section_header(line):
                # 保存前一个段落
                if current_section:
                    structured_text.append({
                        'type': section_type,
                        'page_number': page_number,
                        'content': '\n'.join(current_section),
                        'level': self._get_header_level('\n'.join(current_section)) if section_type == 'header' else 0
                    })
                
                # 保存标题为单独的header
                structured_text.append({
                    'type': 'header',
                    'page_number': page_number,
                    'content': line,
                    'level': self._get_header_level(line)
                })
                
                # 开始新的段落
                current_section = []
                section_type = 'paragraph'
            else:
                current_section.append(line)
        
        # 保存最后一个段落
        if current_section:
            structured_text.append({
                'type': section_type,
                'page_number': page_number,
                'content': '\n'.join(current_section),
                'level': self._get_header_level('\n'.join(current_section)) if section_type == 'header' else 0
            })
        
        return structured_text
    
    def _is_section_header(self, line: str) -> bool:
        """判断是否为章节标题"""
        # 匹配各种章节编号格式
        patterns = [
            r'^\d+\s+.*',  # 1 范围
            r'^\d+\.\d+\s+.*',  # 1.1 职责  
            r'^\d+\.\d+\.\d+\s+.*',  # 1.1.1 具体内容
            r'^第[一二三四五六七八九十\d]+章\s+.*',  # 第一章
            r'^第[一二三四五六七八九十\d]+节\s+.*',  # 第一节
            r'^[一二三四五六七八九十]\s*[、.].*',  # 一、范围
            r'^\([一二三四五六七八九十\d]+\).*',  # (一)内容
        ]
        
        for pattern in patterns:
            if re.match(pattern, line):
                return True
        return False
    
    def _get_header_level(self, header: str) -> int:
        """获取标题级别"""
        if re.match(r'^第[一二三四五六七八九十\d]+章', header):
            return 1
        elif re.match(r'^\d+\s+', header):
            return 2
        elif re.match(r'^\d+\.\d+\s+', header):
            return 3
        elif re.match(r'^\d+\.\d+\.\d+\s+', header):
            return 4
        else:
            return 5
    
    def _extract_tables_from_page(self, page, page_number: int) -> List[Dict[str, Any]]:
        """从页面提取表格"""
        tables = []
        
        try:
            # 使用pdfplumber的表格检测
            page_tables = page.extract_tables()
            
            for table_idx, table_data in enumerate(page_tables):
                if table_data:
                    # 清理表格数据
                    cleaned_table = []
                    for row in table_data:
                        cleaned_row = []
                        for cell in row:
                            if cell:
                                # 清理单元格内容
                                clean_cell = str(cell).strip().replace('\n', ' ')
                                cleaned_row.append(clean_cell)
                            else:
                                cleaned_row.append('')
                        cleaned_table.append(cleaned_row)
                    
                    # 过滤掉空表格
                    if self._is_valid_table(cleaned_table):
                        tables.append({
                            'page_number': page_number,
                            'table_index': table_idx,
                            'data': cleaned_table,
                            'rows': len(cleaned_table),
                            'columns': len(cleaned_table[0]) if cleaned_table else 0,
                            'bbox': self._get_table_bbox(page, table_idx)
                        })
            
            # 如果pdfplumber没找到表格，尝试基于文本模式识别
            if not tables:
                text_tables = self._extract_tables_from_text(page.extract_text(), page_number)
                tables.extend(text_tables)
                
        except Exception as e:
            logger.warning(f"第{page_number}页表格提取失败: {e}")
        
        return tables
    
    def _is_valid_table(self, table_data: List[List[str]]) -> bool:
        """验证表格是否有效"""
        if not table_data or len(table_data) < 2:
            return False
        
        # 检查是否有足够的非空单元格
        non_empty_cells = 0
        total_cells = 0
        
        for row in table_data:
            for cell in row:
                total_cells += 1
                if cell and cell.strip():
                    non_empty_cells += 1
        
        # 至少30%的单元格有内容
        return non_empty_cells / total_cells >= 0.3 if total_cells > 0 else False
    
    def _get_table_bbox(self, page, table_idx: int) -> Dict[str, float]:
        """获取表格边界框"""
        try:
            tables = page.find_tables()
            if table_idx < len(tables):
                bbox = tables[table_idx].bbox
                return {
                    'x0': bbox[0],
                    'y0': bbox[1], 
                    'x1': bbox[2],
                    'y1': bbox[3]
                }
        except:
            pass
        return {}
    
    def _extract_tables_from_text(self, text: str, page_number: int) -> List[Dict[str, Any]]:
        """从文本中识别表格模式"""
        tables = []
        lines = text.split('\n')
        
        # 查找表格模式：连续多行包含制表符或多个空格分隔的数据
        table_lines = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            # 判断是否为表格行
            if self._is_table_line(line):
                table_lines.append(line)
                in_table = True
            else:
                if in_table and len(table_lines) >= 2:
                    # 处理找到的表格
                    table_data = self._parse_text_table(table_lines)
                    if table_data:
                        tables.append({
                            'page_number': page_number,
                            'table_index': len(tables),
                            'data': table_data,
                            'rows': len(table_data),
                            'columns': len(table_data[0]) if table_data else 0,
                            'source': 'text_pattern'
                        })
                
                table_lines = []
                in_table = False
        
        # 处理文档末尾的表格
        if in_table and len(table_lines) >= 2:
            table_data = self._parse_text_table(table_lines)
            if table_data:
                tables.append({
                    'page_number': page_number,
                    'table_index': len(tables),
                    'data': table_data,
                    'rows': len(table_data),
                    'columns': len(table_data[0]) if table_data else 0,
                    'source': 'text_pattern'
                })
        
        return tables
    
    def _is_table_line(self, line: str) -> bool:
        """判断是否为表格行"""
        if not line:
            return False
        
        # 包含多个制表符或连续空格的行
        if '\t' in line or re.search(r'\s{3,}', line):
            # 排除标题行（通常只有少量分隔符）
            separators = line.count('\t') + len(re.findall(r'\s{3,}', line))
            return separators >= 1
        
        return False
    
    def _parse_text_table(self, table_lines: List[str]) -> List[List[str]]:
        """解析文本表格"""
        table_data = []
        
        for line in table_lines:
            # 分割行数据
            if '\t' in line:
                cells = line.split('\t')
            else:
                cells = re.split(r'\s{3,}', line)
            
            # 清理单元格
            cleaned_cells = [cell.strip() for cell in cells if cell.strip()]
            if cleaned_cells:
                table_data.append(cleaned_cells)
        
        return table_data if len(table_data) >= 2 else []
    
    def _extract_images_from_page(self, page, doc, page_number: int) -> List[Dict[str, Any]]:
        """从页面提取图片"""
        images = []
        
        try:
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n < 5:  # 非CMYK图像
                        img_data = pix.tobytes("png")
                        images.append({
                            'page_number': page_number,
                            'image_index': img_index,
                            'data': img_data,
                            'filename': f"page_{page_number}_img_{img_index}.png",
                            'width': pix.width,
                            'height': pix.height,
                            'size_bytes': len(img_data)
                        })
                    pix = None
                except Exception as e:
                    logger.warning(f"无法提取第{page_number}页图片{img_index}: {e}")
                    
        except Exception as e:
            logger.warning(f"第{page_number}页图片提取失败: {e}")
        
        return images
    
    def _post_process_content(self, text_content: List, tables: List, images: List) -> Dict[str, Any]:
        """后处理内容：去重、合并相关内容等"""
        
        # 文本去重和合并
        processed_text = []
        seen_content = set()
        
        for item in text_content:
            content_hash = hash(item['content'])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                processed_text.append(item)
        
        # 表格去重（基于内容相似度）
        processed_tables = []
        for table in tables:
            if not self._is_duplicate_table(table, processed_tables):
                processed_tables.append(table)
        
        return {
            'text_content': processed_text,
            'tables': processed_tables,
            'images': images
        }
    
    def _is_duplicate_table(self, table: Dict, existing_tables: List[Dict]) -> bool:
        """检查表格是否重复"""
        for existing in existing_tables:
            if (table.get('rows') == existing.get('rows') and 
                table.get('columns') == existing.get('columns')):
                
                # 比较前几行内容
                table_preview = str(table['data'][:2])
                existing_preview = str(existing['data'][:2])
                
                if table_preview == existing_preview:
                    return True
        
        return False
    
    def extract_text_from_image(self, image_data: bytes) -> str:
        """从图片中提取文字"""
        try:
            # 将字节数据转换为numpy数组
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # 使用OCR提取文字（兼容不同版本，无需传cls参数）
            try:
                result = self.ocr.ocr(img)
            except TypeError:
                result = self.ocr.ocr(img)
            
            text_list = []
            if result:
                for res_block in result:
                    if res_block:
                        for line in res_block:
                            text_list.append(line[1][0])
            
            return ' '.join(text_list)
        except Exception as e:
            logger.error(f"图片文字识别失败: {e}")
            return ""