"""
Base model client interface.
"""

import logging
from abc import abstractmethod

from ...core.interfaces import ModelClient
from ...core.exceptions import ModelError


logger = logging.getLogger(__name__)


class BaseModelClient(ModelClient):
    """Base implementation for model clients."""
    
    def __init__(self, name: str = None):
        """Initialize base model client."""
        self.name = name or self.__class__.__name__
        self._initialized = False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from the model."""
        if not self.is_available():
            raise ModelError(f"Model client {self.name} is not available")
        
        try:
            logger.debug(f"Generating response with {self.name}")
            response = self._generate_response(prompt, **kwargs)
            logger.debug(f"Generated response of length {len(response)}")
            return response
        except Exception as e:
            logger.error(f"Generation failed in {self.name}: {e}")
            raise ModelError(f"Generation failed: {e}")
    
    @abstractmethod
    def _generate_response(self, prompt: str, **kwargs) -> str:
        """Internal response generation implementation."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model service is available."""
        pass