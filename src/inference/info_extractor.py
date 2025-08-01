"""
大模型信息提取器，用于从标准化的文档数据中提取结构化信息。
"""
import json
import logging
import re
from typing import Dict, Any

from ..data_processing.schemas import StandardizedDocument
from .vllm_client import VLLMInferenceClient
from .prompts import ExtractionPrompts
from .enhanced_content_processor import EnhancedContentProcessor

logger = logging.getLogger(__name__)

class LLMInfoExtractor:
    """
    使用大模型从预处理后的文档中提取结构化信息。
    """

    def __init__(self, vllm_client: VLLMInferenceClient):
        """
        初始化信息提取器。

        Args:
            vllm_client: 用于与VLLM服务交互的客户端实例。
        """
        self.client = vllm_client
        self.prompts = ExtractionPrompts()
        self.content_processor = EnhancedContentProcessor()
        logger.info("LLM信息提取器已初始化。")

    def extract_all_info(self, document: StandardizedDocument) -> Dict[str, Any]:
        """
        执行完整的信息提取流程。

        Args:
            document: 包含标准化数据的Pydantic模型。

        Returns:
            一个包含所有提取信息的字典。
        """
        extracted_data = {}
        
        logger.info(f"开始为文档 '{document.document_info.file_name}' 提取元数据...")
        extracted_data['metadata'] = self._extract_metadata(document)
        
        # 后续可以扩展其他信息的提取，如多模态内容分析等
        # extracted_data['multimodal_analysis'] = self._analyze_multimodal_content(document)

        logger.info("所有信息提取任务完成。")
        return extracted_data

    def _extract_metadata(self, document: StandardizedDocument) -> Dict[str, Any]:
        """
        从文档中提取基础元数据，如标题、编号、日期等。

        Args:
            document: 标准化文档对象。

        Returns:
            一个包含元数据键值对的字典。
        """
        logger.info("🔍 正在为元数据提取获取专门内容...")
        
        # 使用专门的内容提取器获取元数据相关内容
        metadata_content = self.content_processor.extract_content_for_scoring_item(
            document, "metadata"
        )
        
        logger.info(f"元数据内容提取完成，长度: {len(metadata_content)} 字符")
        
        prompt = self.prompts.get_metadata_prompt(metadata_content)
        
        try:
            response_str = self.client.text_analysis(prompt)
            metadata = self._parse_json_response(response_str)
            logger.info(f"成功提取并解析了元数据: {metadata}")
            return metadata
        except Exception as e:
            logger.error(f"提取元数据失败: {e}", exc_info=True)
            return {"error": "提取元数据失败", "details": str(e)}

    def _get_text_summary(self, document: StandardizedDocument, max_pages: int = 3) -> str:
        """
        从文档的前N页生成文本摘要。

        Args:
            document: 标准化文档对象。
            max_pages: 用于生成摘要的最大页数。

        Returns:
            一个拼接了前N页文本内容的字符串。
        """
        summary_parts = []
        for text_item in document.text_content:
            if text_item.page_number <= max_pages:
                summary_parts.append(text_item.content)
        
        summary = "\n".join(summary_parts)
        logger.debug(f"为元数据提取生成了 {len(summary)} 字符的文本摘要。")
        return summary

    def _parse_json_response(self, response_str: str) -> Dict[str, Any]:
        """
        安全地解析可能包含在Markdown代码块中的JSON字符串。

        Args:
            response_str: 模型返回的原始字符串。

        Returns:
            解析后的字典。
            
        Raises:
            ValueError: 如果无法从字符串中解析出有效的JSON。
        """
        try:
            # 尝试直接解析
            return json.loads(response_str)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试从Markdown代码块中提取
            match = re.search(r"```json\n(.*)\n```", response_str, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError as e:
                    logger.error(f"无法解析Markdown代码块中的JSON: {e}")
                    raise ValueError("响应中包含格式错误的JSON代码块。")
            
            logger.error(f"响应既不是有效的JSON，也未包含JSON代码块: {response_str}")
            raise ValueError("模型响应格式不正确，无法解析JSON。")
