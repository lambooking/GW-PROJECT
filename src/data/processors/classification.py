"""
Document classification processor.
"""

import logging
import re
from typing import Tuple, Optional

from .base import BaseDocumentProcessor
from ..schemas import StandardizedDocument


logger = logging.getLogger(__name__)


class DocumentClassifier(BaseDocumentProcessor):
    """Classifier to determine document scenario type."""
    
    def __init__(self):
        """Initialize classifier with scenario patterns."""
        super().__init__()
        
        # Patterns for scenario identification
        self.scenario_patterns = {
            'scenario_1': [
                r'作业指导书',
                r'操作指导',
                r'作业规程',
                r'操作规程',
                r'工作指导',
                r'岗位作业'
            ],
            'scenario_2': [
                r'高后果区',
                r'风险管控',
                r'管控方案',
                r'风险评估',
                r'安全管控',
                r'高风险区域'
            ]
        }
    
    def _process_document(self, document: StandardizedDocument) -> StandardizedDocument:
        """Classify document scenario type."""
        # Get document title and content for classification
        full_text = document.get_full_text()
        title = self._extract_title(document)
        
        # Classify scenario
        scenario_type, confidence = self._classify_scenario(title, full_text)
        
        # Update document info
        document.document_info.scene_type = scenario_type
        document.document_info.scene_name = self._get_scenario_name(scenario_type)
        document.document_info.classification_confidence = confidence
        
        logger.info(f"Classified document as {scenario_type} with confidence {confidence:.2f}")
        
        return document
    
    def _extract_title(self, document: StandardizedDocument) -> str:
        """Extract document title from content."""
        # Look for title in text content
        for content in document.text_content:
            if content.section_type == "title" and content.hierarchy_level == 1:
                return content.content
        
        # Fallback: use first content or filename
        if document.text_content:
            return document.text_content[0].content
        
        return document.document_info.file_name
    
    def _classify_scenario(self, title: str, full_text: str) -> Tuple[str, float]:
        """Classify document scenario based on content."""
        text_to_analyze = f"{title} {full_text[:2000]}"  # Use title + first 2000 chars
        
        scenario_scores = {}
        
        for scenario, patterns in self.scenario_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_to_analyze, re.IGNORECASE))
                score += matches
            
            # Normalize score by number of patterns
            scenario_scores[scenario] = score / len(patterns)
        
        # Find best match
        if not scenario_scores or max(scenario_scores.values()) == 0:
            return 'unknown', 0.0
        
        best_scenario = max(scenario_scores, key=scenario_scores.get)
        confidence = scenario_scores[best_scenario]
        
        # Normalize confidence to 0-1 range
        max_possible_score = 10  # Rough estimate
        confidence = min(confidence / max_possible_score, 1.0)
        
        return best_scenario, confidence
    
    def _get_scenario_name(self, scenario_type: str) -> str:
        """Get human-readable scenario name."""
        scenario_names = {
            'scenario_1': '作业指导书',
            'scenario_2': '高后果区风险管控方案',
            'unknown': '未知类型'
        }
        return scenario_names.get(scenario_type, '未知类型')