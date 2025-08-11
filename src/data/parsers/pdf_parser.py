"""
PDF document parser implementation.
"""

import base64
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from .base import BaseDocumentParser
from ..schemas import DocumentInfo, TextContent, Image, StandardizedDocument
from ...core.exceptions import DocumentProcessingError


logger = logging.getLogger(__name__)


class PDFDocumentParser(BaseDocumentParser):
    """PDF document parser using PyMuPDF."""
    
    def __init__(self, enable_ocr: bool = True, enable_images: bool = True):
        """Initialize PDF parser."""
        super().__init__(enable_ocr, enable_images)
        
        if not PYMUPDF_AVAILABLE:
            raise DocumentProcessingError("PyMuPDF not available. Install with: pip install PyMuPDF")
    
    def supports_format(self, file_path: Path) -> bool:
        """Check if parser supports PDF format."""
        return file_path.suffix.lower() == '.pdf'
    
    def _parse_document(self, file_path: Path) -> StandardizedDocument:
        """Parse PDF document."""
        self._validate_file_size(file_path)
        
        try:
            doc = fitz.open(file_path)
            
            # Extract document info
            document_info = self._extract_document_info(file_path, doc)
            
            # Extract text content
            text_content = self._extract_text_content(doc)
            
            # Extract images if enabled
            images = []
            if self.enable_images:
                images = self._extract_images(doc)
            
            doc.close()
            
            return StandardizedDocument(
                document_info=document_info,
                text_content=text_content,
                images=images,
                raw_content=self._get_raw_text(text_content)
            )
            
        except Exception as e:
            raise DocumentProcessingError(f"PDF parsing error: {e}")
    
    def _extract_document_info(self, file_path: Path, doc: fitz.Document) -> DocumentInfo:
        """Extract document metadata."""
        return DocumentInfo(
            file_name=file_path.name,
            file_path=str(file_path.absolute()),
            total_pages=len(doc),
            file_size=self._get_file_size(file_path),
            processing_timestamp=datetime.now()
        )
    
    def _extract_text_content(self, doc: fitz.Document) -> List[TextContent]:
        """Extract text content from PDF."""
        text_content = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get text blocks
            blocks = page.get_text("blocks")
            
            for block_idx, block in enumerate(blocks):
                if len(block) >= 4 and block[4].strip():  # Has text content
                    text = block[4].strip()
                    
                    # Determine section type
                    section_type = self._determine_section_type(text)
                    
                    content = TextContent(
                        section_type=section_type,
                        content=text,
                        page_number=page_num + 1,
                        word_count=len(text),
                        coordinates={
                            'x0': block[0],
                            'y0': block[1], 
                            'x1': block[2],
                            'y1': block[3]
                        }
                    )
                    
                    text_content.append(content)
        
        return text_content
    
    def _extract_images(self, doc: fitz.Document) -> List[Image]:
        """Extract images from PDF."""
        images = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get image list
            image_list = page.get_images()
            
            for img_idx, img in enumerate(image_list):
                try:
                    # Extract image
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # Not CMYK
                        # Convert to PNG bytes
                        img_data = pix.pil_tobytes(format="PNG")
                        
                        # Encode to base64
                        base64_data = base64.b64encode(img_data).decode('utf-8')
                        
                        image = Image(
                            image_id=f"page_{page_num + 1}_img_{img_idx + 1}",
                            base64_data=base64_data,
                            page_number=page_num + 1
                        )
                        
                        images.append(image)
                    
                    pix = None
                    
                except Exception as e:
                    logger.warning(f"Failed to extract image {img_idx} from page {page_num + 1}: {e}")
                    continue
        
        return images
    
    def _determine_section_type(self, text: str) -> str:
        """Determine section type based on text content."""
        text_lower = text.lower().strip()
        
        # Check for titles (simple heuristic)
        if (len(text) < 100 and 
            (text.startswith(('第', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十')) or
             any(char.isdigit() for char in text[:10]) and '.' in text[:10])):
            return "title"
        
        # Check for table/image captions
        if text_lower.startswith(('表', '图', 'table', 'figure')):
            if '表' in text_lower:
                return "table_caption"
            else:
                return "image_caption"
        
        return "content"
    
    def _get_raw_text(self, text_content: List[TextContent]) -> str:
        """Get raw text from text content."""
        return "\n".join([content.content for content in text_content])