"""
Abstract interfaces and protocols for the RAG Scoring System.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from ..data.schemas import StandardizedDocument, ScoringResult


class DocumentParser(ABC):
    """Abstract base class for document parsers."""
    
    @abstractmethod
    def parse(self, file_path: Union[str, Path]) -> 'StandardizedDocument':
        """Parse a document file into a StandardizedDocument."""
        pass
    
    @abstractmethod
    def supports_format(self, file_path: Union[str, Path]) -> bool:
        """Check if the parser supports the given file format."""
        pass


class DocumentProcessor(ABC):
    """Abstract base class for document processors."""
    
    @abstractmethod
    def process(self, document: 'StandardizedDocument') -> 'StandardizedDocument':
        """Process a standardized document."""
        pass


class ScoringEngine(ABC):
    """Abstract base class for scoring engines."""
    
    @abstractmethod
    def score(self, document: 'StandardizedDocument', **kwargs) -> 'ScoringResult':
        """Score a document and return results."""
        pass
    
    @abstractmethod
    def get_supported_scenarios(self) -> List[str]:
        """Get list of supported scenarios."""
        pass


class KnowledgeBase(ABC):
    """Abstract base class for knowledge bases."""
    
    @abstractmethod
    def add_document(self, document: 'StandardizedDocument', metadata: Optional[Dict] = None) -> str:
        """Add a document to the knowledge base."""
        pass
    
    @abstractmethod
    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant information."""
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional['StandardizedDocument']:
        """Retrieve a document by ID."""
        pass
    
    @abstractmethod
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the knowledge base."""
        pass


class ReportGenerator(ABC):
    """Abstract base class for report generators."""
    
    @abstractmethod
    def generate_report(self, scoring_result: 'ScoringResult', output_path: Path) -> Path:
        """Generate a report from scoring results."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        pass


class ModelClient(ABC):
    """Abstract base class for model clients."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from the model."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model service is available."""
        pass