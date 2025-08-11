"""
DOCX document parser implementation.
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from io import BytesIO

try:
    from docx import Document as DocxDocument
    from docx.shared import Inches
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False

from .base import BaseDocumentParser
from ..schemas import DocumentInfo, TextContent, Table, Image, StandardizedDocument
from ...core.exceptions import DocumentProcessingError


logger = logging.getLogger(__name__)


class DocxDocumentParser(BaseDocumentParser):
    """DOCX document parser using python-docx."""
    
    def __init__(self, enable_ocr: bool = True, enable_images: bool = True):
        """Initialize DOCX parser."""
        super().__init__(enable_ocr, enable_images)
        
        if not PYTHON_DOCX_AVAILABLE:
            raise DocumentProcessingError("python-docx not available. Install with: pip install python-docx")
    
    def supports_format(self, file_path: Path) -> bool:
        """Check if parser supports DOCX format."""
        return file_path.suffix.lower() in ['.docx', '.doc']
    
    def _parse_document(self, file_path: Path) -> StandardizedDocument:
        """Parse DOCX document."""
        self._validate_file_size(file_path)
        
        try:
            doc = DocxDocument(file_path)
            
            # Extract document info
            document_info = self._extract_document_info(file_path, doc)
            
            # Extract text content
            text_content = self._extract_text_content(doc)
            
            # Extract tables
            tables = self._extract_tables(doc)
            
            # Extract images if enabled  
            images = []
            if self.enable_images:
                images = self._extract_images(doc)
            
            return StandardizedDocument(
                document_info=document_info,
                text_content=text_content,
                tables=tables,
                images=images,
                raw_content=self._get_raw_text(text_content)
            )
            
        except Exception as e:
            raise DocumentProcessingError(f"DOCX parsing error: {e}")
    
    def _extract_document_info(self, file_path: Path, doc: DocxDocument) -> DocumentInfo:
        """Extract document metadata."""
        # Estimate page count (rough approximation)
        total_chars = sum(len(p.text) for p in doc.paragraphs)
        estimated_pages = max(1, total_chars // 2000)  # Rough estimate
        
        return DocumentInfo(
            file_name=file_path.name,
            file_path=str(file_path.absolute()),
            total_pages=estimated_pages,
            file_size=self._get_file_size(file_path),
            processing_timestamp=datetime.now()
        )
    
    def _extract_text_content(self, doc: DocxDocument) -> List[TextContent]:
        """Extract text content from DOCX."""
        text_content = []
        current_page = 1  # We can't easily determine actual page numbers in DOCX
        
        for para_idx, paragraph in enumerate(doc.paragraphs):
            if paragraph.text.strip():
                # Determine section type and hierarchy
                section_type, hierarchy_level = self._analyze_paragraph(paragraph)
                
                content = TextContent(
                    section_type=section_type,
                    content=paragraph.text.strip(),
                    page_number=current_page,
                    hierarchy_level=hierarchy_level,
                    word_count=len(paragraph.text.strip())
                )
                
                text_content.append(content)
                
                # Simple page estimation (every ~20 paragraphs = 1 page)
                if (para_idx + 1) % 20 == 0:
                    current_page += 1
        
        return text_content
    
    def _extract_tables(self, doc: DocxDocument) -> List[Table]:
        """Extract tables from DOCX."""
        tables = []
        
        for table_idx, table in enumerate(doc.tables):
            try:
                # Extract headers (first row)
                headers = []
                if len(table.rows) > 0:
                    headers = [cell.text.strip() for cell in table.rows[0].cells]
                
                # Extract data (remaining rows)
                data = []
                for row in table.rows[1:]:
                    row_data = [cell.text.strip() for cell in row.cells]
                    data.append(row_data)
                
                table_obj = Table(
                    table_id=f"table_{table_idx + 1}",
                    headers=headers,
                    data=data,
                    page_number=1  # We can't determine actual page in DOCX easily
                )
                
                tables.append(table_obj)
                
            except Exception as e:
                logger.warning(f"Failed to extract table {table_idx}: {e}")
                continue
        
        return tables
    
    def _extract_images(self, doc: DocxDocument) -> List[Image]:
        """Extract images from DOCX."""
        images = []
        
        try:
            # Get document part
            document_part = doc.part
            
            # Get all image parts
            for rel in document_part.rels.values():
                if "image" in rel.target_ref:
                    try:
                        # Get image binary data
                        image_part = rel.target_part
                        image_data = image_part.blob
                        
                        # Encode to base64
                        base64_data = base64.b64encode(image_data).decode('utf-8')
                        
                        image = Image(
                            image_id=f"docx_img_{len(images) + 1}",
                            base64_data=base64_data,
                            page_number=1  # Can't determine actual page easily
                        )
                        
                        images.append(image)
                        
                    except Exception as e:
                        logger.warning(f"Failed to extract image: {e}")
                        continue
                        
        except Exception as e:
            logger.warning(f"Failed to extract images from DOCX: {e}")
        
        return images
    
    def _analyze_paragraph(self, paragraph) -> tuple[str, Optional[int]]:
        """Analyze paragraph to determine type and hierarchy."""
        text = paragraph.text.strip()
        
        # Check if it's a heading
        hierarchy_level = None
        section_type = "content"
        
        # Check paragraph style for headings
        if paragraph.style.name.startswith('Heading'):
            section_type = "title"
            try:
                # Extract heading level from style name
                hierarchy_level = int(paragraph.style.name.split()[-1])
            except:
                hierarchy_level = 1
        
        # Heuristic checks for titles
        elif (len(text) < 100 and 
              (text.startswith(('第', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十')) or
               any(char.isdigit() for char in text[:10]) and '.' in text[:10])):
            section_type = "title"
            hierarchy_level = 1
        
        # Check for table/image captions
        elif text.lower().startswith(('表', '图', 'table', 'figure')):
            if '表' in text.lower():
                section_type = "table_caption"
            else:
                section_type = "image_caption"
        
        return section_type, hierarchy_level
    
    def _get_raw_text(self, text_content: List[TextContent]) -> str:
        """Get raw text from text content."""
        return "\n".join([content.content for content in text_content])