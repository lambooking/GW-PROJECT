"""
Report generation service that integrates with the refactored system.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..utils.html_report_generator import HTMLReportGenerator
from ..data.schemas import ScoringResult, StandardizedDocument
from ..core.exceptions import ServiceError

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating various report formats."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize report service.
        
        Args:
            output_dir: Directory for saving reports. Defaults to output/reports/
        """
        self.output_dir = output_dir or Path("output/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._html_generator = HTMLReportGenerator()
        
        logger.info(f"ReportService initialized with output directory: {self.output_dir}")
    
    def generate_json_report(self, scoring_result: ScoringResult, 
                           output_path: Optional[str] = None) -> str:
        """Generate JSON format report.
        
        Args:
            scoring_result: Scoring result to convert
            output_path: Custom output path. If None, auto-generates filename
            
        Returns:
            Path to generated JSON file
        """
        try:
            # Convert scoring result to JSON format
            json_data = self._convert_scoring_result_to_json(scoring_result)
            
            # Generate filename if not provided
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"rag_scoring_report_{scoring_result.document_info.file_name}_{timestamp}.json"
                output_path = str(self.output_dir / filename)
            
            # Write JSON file
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"JSON report generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate JSON report: {e}")
            raise ServiceError(f"JSON report generation failed: {e}")
    
    def generate_html_report(self, scoring_result: ScoringResult,
                           output_path: Optional[str] = None) -> str:
        """Generate HTML format report.
        
        Args:
            scoring_result: Scoring result to convert
            output_path: Custom output path. If None, auto-generates filename
            
        Returns:
            Path to generated HTML file
        """
        try:
            # Convert scoring result to JSON format first
            json_data = self._convert_scoring_result_to_json(scoring_result)
            
            # Generate filename if not provided
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"rag_scoring_report_{scoring_result.document_info.file_name}_{timestamp}.html"
                output_path = str(self.output_dir / filename)
            
            # Generate HTML report using existing generator
            html_path = self._html_generator.generate_html_report(json_data, output_path)
            
            logger.info(f"HTML report generated: {html_path}")
            return html_path
            
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            raise ServiceError(f"HTML report generation failed: {e}")
    
    def generate_complete_report(self, scoring_result: ScoringResult,
                               base_filename: Optional[str] = None) -> Dict[str, str]:
        """Generate both JSON and HTML reports.
        
        Args:
            scoring_result: Scoring result to convert
            base_filename: Base filename (without extension)
            
        Returns:
            Dictionary with paths to generated files
        """
        try:
            # Generate base filename if not provided
            if base_filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                base_filename = f"rag_scoring_report_{scoring_result.document_info.file_name}_{timestamp}"
            
            # Generate both formats
            json_path = self.generate_json_report(
                scoring_result, 
                str(self.output_dir / f"{base_filename}.json")
            )
            
            html_path = self.generate_html_report(
                scoring_result,
                str(self.output_dir / f"{base_filename}.html")
            )
            
            result = {
                "json_report": json_path,
                "html_report": html_path
            }
            
            logger.info(f"Complete report generated: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate complete report: {e}")
            raise ServiceError(f"Complete report generation failed: {e}")
    
    def batch_convert_to_html(self, json_reports_dir: str, 
                            html_output_dir: Optional[str] = None) -> List[str]:
        """Batch convert JSON reports to HTML.
        
        Args:
            json_reports_dir: Directory containing JSON reports
            html_output_dir: Output directory for HTML reports
            
        Returns:
            List of generated HTML file paths
        """
        try:
            html_dir = html_output_dir or str(self.output_dir / "html_batch")
            return self._html_generator.batch_convert_reports(json_reports_dir, html_dir)
            
        except Exception as e:
            logger.error(f"Batch conversion failed: {e}")
            raise ServiceError(f"Batch conversion failed: {e}")
    
    def _convert_scoring_result_to_json(self, scoring_result: ScoringResult) -> Dict[str, Any]:
        """Convert ScoringResult to JSON format compatible with HTML generator.
        
        Args:
            scoring_result: ScoringResult instance
            
        Returns:
            JSON-compatible dictionary
        """
        try:
            # Document info
            doc_info = {
                "file_name": scoring_result.document_info.file_name,
                "file_path": scoring_result.document_info.file_path,
                "scene_name": scoring_result.scenario,
                "scene_type": scoring_result.document_info.scene_type,
                "total_pages": scoring_result.document_info.total_pages
            }
            
            # Summary
            summary = {
                "total_score": scoring_result.total_score,
                "max_total_score": scoring_result.max_total_score,
                "percentage": scoring_result.score_percentage,
                "grade": self._calculate_grade(scoring_result.score_percentage),
                "scoring_criteria_count": len(scoring_result.score_items),
                "overall_assessment": scoring_result.summary or "综合评估完成"
            }
            
            # Detailed scores
            detailed_scores = {}
            score_breakdown = {}
            
            for i, item in enumerate(scoring_result.score_items):
                key = f"criterion_{i+1}"
                
                detailed_scores[key] = {
                    "name": item.name,
                    "score": item.score,
                    "max_score": item.max_score,
                    "reasoning": item.reason,
                    "evaluation_focus": ", ".join(item.evidence) if item.evidence else "综合评估",
                    "suggestions": item.suggestions
                }
                
                score_breakdown[key] = {
                    "weight": item.weight,
                    "weighted_score": item.score * item.weight,
                    "percentage": (item.score / item.max_score * 100) if item.max_score > 0 else 0
                }
            
            # Complete JSON structure
            json_data = {
                "document_info": doc_info,
                "summary": summary,
                "detailed_scores": detailed_scores,
                "score_breakdown": score_breakdown,
                "scoring_timestamp": scoring_result.timestamp.isoformat(),
                "processing_time": scoring_result.processing_time,
                "system_info": {
                    "version": "2.0.0",
                    "engine": "RAG Intelligent Scoring System",
                    "scenario": scoring_result.scenario
                }
            }
            
            return json_data
            
        except Exception as e:
            logger.error(f"Failed to convert scoring result: {e}")
            raise ServiceError(f"Scoring result conversion failed: {e}")
    
    def _calculate_grade(self, percentage: float) -> str:
        """Calculate letter grade from percentage.
        
        Args:
            percentage: Score percentage (0-100)
            
        Returns:
            Grade string
        """
        if percentage >= 90:
            return "优秀"
        elif percentage >= 80:
            return "良好"
        elif percentage >= 70:
            return "中等"
        elif percentage >= 60:
            return "及格"
        else:
            return "不及格"