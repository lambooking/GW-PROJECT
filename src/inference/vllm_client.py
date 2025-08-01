"""
VLLM 推理客户端，用于与部署的VLLM OpenAI兼容API进行交互。
"""
import logging
from typing import List, Dict, Any

from openai import OpenAI, APIError
import backoff

logger = logging.getLogger(__name__)

class VLLMInferenceClient:
    """
    一个封装了对VLLM OpenAI API调用的客户端。
    提供了文本和多模态分析的功能，并包含了重试机制。
    """

    def __init__(self, base_url: str = "http://localhost:8000/v1", api_key: str = "EMPTY", model_name: str = "qwen2.5-vl-3b"):
        """
        初始化客户端。

        Args:
            base_url: VLLM服务的URL。
            api_key: API密钥，对于本地VLLM服务，通常为"EMPTY"。
            model_name: 要使用的模型名称。
        """
        # 禁用代理，确保能直接连接到本地VLLM服务
        import httpx
        import os
        
        # 临时清除代理环境变量
        proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']
        original_proxies = {}
        for var in proxy_vars:
            if var in os.environ:
                original_proxies[var] = os.environ[var]
                del os.environ[var]
        
        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        finally:
            # 恢复原始代理设置
            for var, value in original_proxies.items():
                os.environ[var] = value
        self.model_name = model_name
        logger.info(f"VLLM客户端已初始化，目标URL: {base_url}, 模型: {model_name}")

    @backoff.on_exception(backoff.expo, APIError, max_tries=3)
    def text_analysis(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.1) -> str:
        """
        对纯文本进行分析。

        Args:
            prompt: 发送给模型的Prompt字符串。
            max_tokens: 生成的最大token数。
            temperature: 控制生成文本的随机性，值越低越确定。

        Returns:
            模型返回的文本内容。
        
        Raises:
            APIError: 如果API调用在重试后仍然失败。
        """
        try:
            logger.debug(f"向VLLM发送文本分析请求，Prompt长度: {len(prompt)}")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9
            )
            content = response.choices[0].message.content
            logger.debug(f"收到VLLM文本分析响应，内容长度: {len(content)}")
            return content
        except APIError as e:
            logger.error(f"VLLM文本分析API请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"处理VLLM文本分析时发生未知错误: {e}")
            raise

    @backoff.on_exception(backoff.expo, APIError, max_tries=3)
    def multimodal_analysis(self, text_prompt: str, images_base64: List[str], max_tokens: int = 2048) -> str:
        """
        对文本和图片进行多模态分析。

        Args:
            text_prompt: 与图片一起发送的文本Prompt。
            images_base64: Base64编码的图片字符串列表。
            max_tokens: 生成的最大token数。

        Returns:
            模型返回的文本内容。
            
        Raises:
            APIError: 如果API调用在重试后仍然失败。
        """
        try:
            logger.debug(f"向VLLM发送多模态分析请求，文本长度: {len(text_prompt)}, 图片数量: {len(images_base64)}")
            
            content: List[Dict[str, Any]] = [{"type": "text", "text": text_prompt}]
            for img_base64 in images_base64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                })

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": content}],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            result_content = response.choices[0].message.content
            logger.debug(f"收到VLLM多模态分析响应，内容长度: {len(result_content)}")
            return result_content
        except APIError as e:
            logger.error(f"VLLM多模态分析API请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"处理VLLM多模态分析时发生未知错误: {e}")
            raise
