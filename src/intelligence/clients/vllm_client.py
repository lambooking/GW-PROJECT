"""
VLLM client for inference with OpenAI-compatible API.
"""

import logging
from typing import List, Dict, Any, Optional
import os

try:
    from openai import OpenAI, APIError
    import backoff
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    
from .base import BaseModelClient
from ...core.exceptions import ModelError, ConfigurationError
from ...config.schemas import VLLMConfig


logger = logging.getLogger(__name__)


class VLLMClient(BaseModelClient):
    """Client for VLLM inference service with OpenAI-compatible API."""
    
    def __init__(self, config: VLLMConfig):
        """Initialize VLLM client."""
        super().__init__("VLLMClient")
        
        if not OPENAI_AVAILABLE:
            raise ConfigurationError("OpenAI library not available. Install with: pip install openai")
        
        self.config = config
        self._client: Optional[OpenAI] = None
        self._setup_client()
    
    def _setup_client(self) -> None:
        """Setup OpenAI client with proxy handling."""
        # Temporarily disable proxies for local VLLM connection
        proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']
        original_proxies = {}
        
        for var in proxy_vars:
            if var in os.environ:
                original_proxies[var] = os.environ[var]
                del os.environ[var]
        
        try:
            base_url = f"http://{self.config.host}:{self.config.port}/v1"
            api_key = self.config.api_key or "EMPTY"
            
            self._client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=self.config.timeout
            )
            
            logger.info(f"VLLM client initialized: {base_url}, model: {self.config.model_name}")
            
        finally:
            # Restore original proxy settings
            for var, value in original_proxies.items():
                os.environ[var] = value
    
    def is_available(self) -> bool:
        """Check if VLLM service is available."""
        try:
            # Simple test call
            response = self._client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
                timeout=5
            )
            return True
        except Exception as e:
            logger.warning(f"VLLM service not available: {e}")
            return False
    
    @backoff.on_exception(backoff.expo, APIError, max_tries=3, max_time=60)
    def _generate_response(self, prompt: str, **kwargs) -> str:
        """Generate response from VLLM."""
        try:
            max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
            temperature = kwargs.get('temperature', self.config.temperature)
            images = kwargs.get('images', [])
            
            if images:
                return self._multimodal_analysis(prompt, images, max_tokens, temperature)
            else:
                return self._text_analysis(prompt, max_tokens, temperature)
                
        except APIError as e:
            logger.error(f"VLLM API error: {e}")
            raise ModelError(f"VLLM API error: {e}")
        except Exception as e:
            logger.error(f"VLLM generation error: {e}")
            raise ModelError(f"VLLM generation error: {e}")
    
    def _text_analysis(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Perform text-only analysis."""
        logger.debug(f"VLLM text analysis request, prompt length: {len(prompt)}")
        
        response = self._client.chat.completions.create(
            model=self.config.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9
        )
        
        content = response.choices[0].message.content
        logger.debug(f"VLLM text analysis response length: {len(content)}")
        return content
    
    def _multimodal_analysis(
        self, 
        text_prompt: str, 
        images_base64: List[str], 
        max_tokens: int, 
        temperature: float
    ) -> str:
        """Perform multimodal analysis with text and images."""
        logger.debug(f"VLLM multimodal analysis: text={len(text_prompt)}, images={len(images_base64)}")
        
        content: List[Dict[str, Any]] = [{"type": "text", "text": text_prompt}]
        
        for img_base64 in images_base64:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_base64}"}
            })
        
        response = self._client.chat.completions.create(
            model=self.config.model_name,
            messages=[{"role": "user", "content": content}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        result_content = response.choices[0].message.content
        logger.debug(f"VLLM multimodal analysis response length: {len(result_content)}")
        return result_content
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on VLLM service."""
        try:
            start_time = __import__('time').time()
            response = self._client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": "Health check"}],
                max_tokens=10,
                timeout=10
            )
            response_time = (__import__('time').time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "model": self.config.model_name,
                "response_time_ms": round(response_time, 2),
                "base_url": f"http://{self.config.host}:{self.config.port}/v1"
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e),
                "model": self.config.model_name,
                "base_url": f"http://{self.config.host}:{self.config.port}/v1"
            }