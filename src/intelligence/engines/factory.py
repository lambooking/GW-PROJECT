"""
Factory for creating scoring engines.
"""

import logging
from typing import Dict, Type, Optional

from .rag_scoring import RAGScoringEngine
from ...core.interfaces import ScoringEngine
from ...core.exceptions import ConfigurationError
from ...config.schemas import Config


logger = logging.getLogger(__name__)


class ScoringEngineFactory:
    """Factory for creating scoring engines."""
    
    _engines: Dict[str, Type[ScoringEngine]] = {
        'rag': RAGScoringEngine,
        'default': RAGScoringEngine
    }
    
    @classmethod
    def create_engine(
        cls, 
        engine_type: str = "rag",
        config: Optional[Config] = None,
        **kwargs
    ) -> ScoringEngine:
        """Create scoring engine of specified type."""
        engine_type = engine_type.lower()
        
        if engine_type not in cls._engines:
            raise ConfigurationError(
                f"Unknown engine type: {engine_type}. "
                f"Available types: {list(cls._engines.keys())}"
            )
        
        engine_class = cls._engines[engine_type]
        
        try:
            if config:
                engine = engine_class(config, **kwargs)
            else:
                engine = engine_class(**kwargs)
            
            logger.info(f"Created scoring engine: {engine_class.__name__}")
            return engine
            
        except Exception as e:
            raise ConfigurationError(f"Failed to create engine {engine_type}: {e}")
    
    @classmethod
    def register_engine(cls, name: str, engine_class: Type[ScoringEngine]) -> None:
        """Register a new scoring engine type."""
        cls._engines[name.lower()] = engine_class
        logger.info(f"Registered scoring engine: {name}")
    
    @classmethod
    def get_available_engines(cls) -> list[str]:
        """Get list of available engine types."""
        return list(cls._engines.keys())