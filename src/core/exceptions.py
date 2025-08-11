"""
Custom exceptions for the RAG Scoring System.
"""

class RAGScoringError(Exception):
    """Base exception class for RAG Scoring System."""
    pass


class ConfigurationError(RAGScoringError):
    """Raised when there's an error in configuration."""
    pass


class DocumentProcessingError(RAGScoringError):
    """Raised when there's an error processing documents."""
    pass


class ScoringError(RAGScoringError):
    """Raised when there's an error during scoring."""
    pass


class KnowledgeBaseError(RAGScoringError):
    """Raised when there's an error with knowledge base operations."""
    pass


class ModelError(RAGScoringError):
    """Raised when there's an error with model inference."""
    pass


class ValidationError(RAGScoringError):
    """Raised when data validation fails."""
    pass


class ServiceError(RAGScoringError):
    """Raised when there's an error in service operations."""
    pass