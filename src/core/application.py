"""
Core application class for the RAG Scoring System.
"""

import logging
from typing import Dict, List, Optional, Union, TYPE_CHECKING, Any
from pathlib import Path

from .interfaces import DocumentParser, ScoringEngine, KnowledgeBase, ReportGenerator
from .exceptions import RAGScoringError, ConfigurationError

if TYPE_CHECKING:
    from ..config import ConfigManager
    from ..data.schemas import StandardizedDocument, ScoringResult


logger = logging.getLogger(__name__)


class RAGScoringApplication:
    """Main application class for the RAG Scoring System."""
    
    def __init__(self, config_manager: 'ConfigManager'):
        """Initialize the application with configuration."""
        self.config = config_manager
        self._parsers: Dict[str, DocumentParser] = {}
        self._scoring_engines: Dict[str, ScoringEngine] = {}
        self._knowledge_base: Optional[KnowledgeBase] = None
        self._report_generators: Dict[str, ReportGenerator] = {}
        
        # Initialize report service lazily to avoid circular imports
        self._report_service = None
        
        logger.info("RAG Scoring Application initialized")
    
    def _get_report_service(self):
        """Lazily initialize report service to avoid circular imports."""
        if self._report_service is None:
            from ..services.report_service import ReportService
            reports_dir = Path(self.config.get("output.reports_dir", "output/reports"))
            self._report_service = ReportService(reports_dir)
        return self._report_service
    
    def register_parser(self, name: str, parser: DocumentParser) -> None:
        """Register a document parser."""
        self._parsers[name] = parser
        logger.debug(f"Registered parser: {name}")
    
    def register_scoring_engine(self, name: str, engine: ScoringEngine) -> None:
        """Register a scoring engine."""
        self._scoring_engines[name] = engine
        logger.debug(f"Registered scoring engine: {name}")
    
    def set_knowledge_base(self, knowledge_base: KnowledgeBase) -> None:
        """Set the knowledge base."""
        self._knowledge_base = knowledge_base
        logger.debug("Knowledge base set")
    
    def register_report_generator(self, format_name: str, generator: ReportGenerator) -> None:
        """Register a report generator."""
        self._report_generators[format_name] = generator
        logger.debug(f"Registered report generator: {format_name}")
    
    def get_suitable_parser(self, file_path: Union[str, Path]) -> DocumentParser:
        """Get a suitable parser for the given file."""
        file_path = Path(file_path)
        
        for parser in self._parsers.values():
            if parser.supports_format(file_path):
                return parser
        
        raise RAGScoringError(f"No suitable parser found for file: {file_path}")
    
    def parse_document(self, file_path: Union[str, Path]) -> 'StandardizedDocument':
        """Parse a document file."""
        try:
            parser = self.get_suitable_parser(file_path)
            document = parser.parse(file_path)
            logger.info(f"Document parsed successfully: {file_path}")
            return document
        except Exception as e:
            logger.error(f"Failed to parse document {file_path}: {e}")
            raise
    
    def score_document(
        self, 
        document: 'StandardizedDocument',
        engine_name: Optional[str] = None
    ) -> 'ScoringResult':
        """Score a document using the specified or default engine."""
        try:
            if engine_name:
                if engine_name not in self._scoring_engines:
                    raise RAGScoringError(f"Scoring engine not found: {engine_name}")
                engine = self._scoring_engines[engine_name]
            else:
                # Use the first available engine as default
                if not self._scoring_engines:
                    raise ConfigurationError("No scoring engines registered")
                engine = next(iter(self._scoring_engines.values()))
            
            result = engine.score(document, knowledge_base=self._knowledge_base)
            logger.info(f"Document scored successfully using engine: {engine_name or 'default'}")
            return result
        except Exception as e:
            logger.error(f"Failed to score document: {e}")
            raise
    
    def generate_report(
        self, 
        scoring_result: 'ScoringResult',
        output_path: Union[str, Path],
        format_name: str = "html"
    ) -> Path:
        """Generate a report from scoring results."""
        try:
            if format_name not in self._report_generators:
                raise RAGScoringError(f"Report generator not found: {format_name}")
            
            generator = self._report_generators[format_name]
            report_path = generator.generate_report(scoring_result, Path(output_path))
            logger.info(f"Report generated successfully: {report_path}")
            return report_path
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise
    
    def generate_html_report(
        self,
        scoring_result: 'ScoringResult',
        output_path: Optional[Union[str, Path]] = None
    ) -> str:
        """Generate HTML report using integrated HTML generator."""
        try:
            report_service = self._get_report_service()
            html_path = report_service.generate_html_report(
                scoring_result, 
                str(output_path) if output_path else None
            )
            logger.info(f"HTML report generated: {html_path}")
            return html_path
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
            raise
    
    def generate_json_report(
        self,
        scoring_result: 'ScoringResult', 
        output_path: Optional[Union[str, Path]] = None
    ) -> str:
        """Generate JSON report."""
        try:
            report_service = self._get_report_service()
            json_path = report_service.generate_json_report(
                scoring_result,
                str(output_path) if output_path else None
            )
            logger.info(f"JSON report generated: {json_path}")
            return json_path
        except Exception as e:
            logger.error(f"Failed to generate JSON report: {e}")
            raise
    
    def generate_complete_reports(
        self,
        scoring_result: 'ScoringResult',
        base_filename: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate both JSON and HTML reports."""
        try:
            report_service = self._get_report_service()
            reports = report_service.generate_complete_report(
                scoring_result,
                base_filename
            )
            logger.info(f"Complete reports generated: {reports}")
            return reports
        except Exception as e:
            logger.error(f"Failed to generate complete reports: {e}")
            raise
    
    def process_document_complete(
        self,
        file_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        engine_name: Optional[str] = None,
        generate_html: bool = True,
        generate_json: bool = True
    ) -> Dict[str, Any]:
        """Complete pipeline: parse -> score -> generate reports with HTML support."""
        
        try:
            # Parse document
            document = self.parse_document(file_path)
            
            # Score document
            scoring_result = self.score_document(document, engine_name)
            
            # Generate reports using integrated report service
            if generate_html or generate_json:
                base_filename = f"rag_scoring_report_{Path(file_path).stem}"
                
                if generate_html and generate_json:
                    # Generate both formats
                    reports = self.generate_complete_reports(scoring_result, base_filename)
                elif generate_html:
                    # Generate only HTML
                    html_path = self.generate_html_report(scoring_result)
                    reports = {"html_report": html_path}
                elif generate_json:
                    # Generate only JSON
                    json_path = self.generate_json_report(scoring_result)
                    reports = {"json_report": json_path}
                else:
                    reports = {}
            else:
                reports = {}
            
            logger.info(f"Complete processing finished for: {file_path}")
            return {
                "scoring_result": scoring_result,
                "reports": reports,
                "document": document
            }
        except Exception as e:
            logger.error(f"Failed to process document completely: {e}")
            raise
    
    def add_to_knowledge_base(self, document: 'StandardizedDocument', metadata: Optional[Dict] = None) -> str:
        """Add a document to the knowledge base."""
        if not self._knowledge_base:
            raise ConfigurationError("Knowledge base not configured")
        
        try:
            doc_id = self._knowledge_base.add_document(document, metadata)
            logger.info(f"Document added to knowledge base: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to add document to knowledge base: {e}")
            raise
    
    def query_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict]:
        """Query the knowledge base."""
        if not self._knowledge_base:
            raise ConfigurationError("Knowledge base not configured")
        
        try:
            results = self._knowledge_base.query(query, top_k)
            logger.debug(f"Knowledge base query returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Failed to query knowledge base: {e}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status information."""
        return {
            "parsers": list(self._parsers.keys()),
            "scoring_engines": list(self._scoring_engines.keys()),
            "knowledge_base": self._knowledge_base is not None,
            "report_generators": list(self._report_generators.keys()),
            "report_service": self._report_service is not None,
            "html_generation": True,  # Always available with integrated service
            "config": self.config.get_summary()
        }