"""
Content enhancement processor for improving document structure.
"""

import logging
import re
from typing import List

from .base import BaseDocumentProcessor
from ..schemas import StandardizedDocument, TextContent


logger = logging.getLogger(__name__)


class ContentEnhancer(BaseDocumentProcessor):
    """Enhancer for improving document content structure and metadata."""
    
    def __init__(self):
        """Initialize enhancer."""
        super().__init__()
    
    def _process_document(self, document: StandardizedDocument) -> StandardizedDocument:
        """Enhance document content structure."""
        # Enhance text content
        document.text_content = self._enhance_text_content(document.text_content)
        
        # Enhance section names
        self._enhance_section_names(document.text_content)
        
        # Clean up content
        document.text_content = self._cleanup_content(document.text_content)
        
        logger.debug(f"Enhanced document content with {len(document.text_content)} text sections")
        
        return document
    
    def _enhance_text_content(self, text_content: List[TextContent]) -> List[TextContent]:
        """Enhance text content with better structure analysis."""
        enhanced_content = []
        
        for content in text_content:
            # Re-analyze section type with more sophisticated rules
            enhanced_type = self._analyze_section_type(content.content, content.section_type)
            content.section_type = enhanced_type
            
            # Improve hierarchy level detection
            if content.section_type == "title":
                content.hierarchy_level = self._detect_hierarchy_level(content.content)
            
            enhanced_content.append(content)
        
        return enhanced_content
    
    def _analyze_section_type(self, text: str, current_type: str) -> str:
        """Analyze section type with improved heuristics."""
        text_lower = text.lower().strip()
        
        # More sophisticated title detection
        if self._is_title(text):
            return "title"
        
        # Table caption detection
        if re.match(r'表\s*\d+', text) or text_lower.startswith('table'):
            return "table_caption"
        
        # Image caption detection
        if re.match(r'图\s*\d+', text) or text_lower.startswith(('figure', 'fig')):
            return "image_caption"
        
        # List item detection
        if re.match(r'^\s*[（\(]?[a-zA-Z0-9一二三四五六七八九十]+[）\)]', text):
            return "list_item"
        
        # Keep original type if no better match
        return current_type
    
    def _is_title(self, text: str) -> bool:
        """Improved title detection."""
        text = text.strip()
        
        # Length check
        if len(text) > 200:
            return False
        
        # Pattern matching
        title_patterns = [
            r'^\d+(\.\d+)*\s+',  # 1.1, 1.2.1, etc.
            r'^[一二三四五六七八九十]+[、．]',  # Chinese numbers
            r'^第[一二三四五六七八九十]+章',  # Chapter indicators
            r'^附录[A-Z]',  # Appendix
            r'^[A-Z]\s*\.',  # A., B., etc.
        ]
        
        for pattern in title_patterns:
            if re.match(pattern, text):
                return True
        
        # Check for common title words
        title_indicators = [
            '目录', '概述', '总则', '职责', '作业内容', '操作步骤', '安全要求',
            '应急预案', '记录', '附录', '附件', '参考', '标准', '规范'
        ]
        
        for indicator in title_indicators:
            if indicator in text and len(text) < 50:
                return True
        
        return False
    
    def _detect_hierarchy_level(self, text: str) -> int:
        """Detect hierarchy level of title."""
        text = text.strip()
        
        # Check for numbered hierarchy (1, 1.1, 1.1.1, etc.)
        match = re.match(r'^(\d+(?:\.\d+)*)', text)
        if match:
            return len(match.group(1).split('.'))
        
        # Check for Chinese numbers
        if re.match(r'^第?[一二三四五六七八九十]+章', text):
            return 1
        
        if re.match(r'^[一二三四五六七八九十]+[、.]', text):
            return 2
        
        # Check for appendix
        if re.match(r'^附录[A-Z]', text):
            return 1
        
        # Default level
        return 1
    
    def _enhance_section_names(self, text_content: List[TextContent]) -> None:
        """Extract and assign section names to content."""
        current_section = None
        
        for content in text_content:
            if content.section_type == "title":
                current_section = content.content
            elif current_section and not content.section_name:
                content.section_name = current_section
    
    def _cleanup_content(self, text_content: List[TextContent]) -> List[TextContent]:
        """Clean up and filter content."""
        cleaned_content = []
        
        for content in text_content:
            # Skip very short or empty content
            if len(content.content.strip()) < 3:
                continue
            
            # Clean up whitespace
            content.content = re.sub(r'\s+', ' ', content.content.strip())
            
            # Update word count
            content.word_count = len(content.content)
            
            cleaned_content.append(content)
        
        return cleaned_content