"""
简单评分引擎，用于对文档进行智能评分。
"""
import logging
from typing import Dict, Any, List

from ..data_processing.schemas import StandardizedDocument
from .vllm_client import VLLMInferenceClient
from .prompts import ScoringPrompts
from .enhanced_content_processor import EnhancedContentProcessor

logger = logging.getLogger(__name__)

class SimpleScoringEngine:
    """
    简单的评分引擎，使用大模型对文档进行评分。
    这是第一阶段的基础实现，后续会扩展为更复杂的评分系统。
    """

    def __init__(self, vllm_client: VLLMInferenceClient):
        """
        初始化评分引擎。

        Args:
            vllm_client: 用于与VLLM服务交互的客户端实例。
        """
        self.client = vllm_client
        self.scoring_prompts = ScoringPrompts()
        self.content_processor = EnhancedContentProcessor()
        
        # 场景一（作业指导书）的必需章节
        self.required_sections_scenario_one = [
            "目录", "范围", "职责", "作业内容", "相关文件", "记录文件"
        ]
        
        logger.info("简单评分引擎已初始化。")

    def score_document(self, document: StandardizedDocument, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        对文档进行完整评分。

        Args:
            document: 标准化的文档数据。
            extracted_info: 从文档中提取的信息。

        Returns:
            包含评分结果的字典。
        """
        try:
            logger.info(f"开始对文档 '{document.document_info.file_name}' 进行评分...")
            
            # 根据场景类型选择评分策略
            scene_type = document.document_info.scene_type
            if scene_type == "scenario_one":
                return self._score_scenario_one(document, extracted_info)
            elif scene_type == "scenario_two":
                # 暂时使用相同的评分逻辑，后续可以扩展
                return self._score_scenario_one(document, extracted_info)
            else:
                return self._score_unknown_scenario(document, extracted_info)
                
        except Exception as e:
            logger.error(f"评分过程中发生错误: {e}", exc_info=True)
            return {
                "error": "评分失败",
                "details": str(e),
                "total_score": 0
            }

    def _score_scenario_one(self, document: StandardizedDocument, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        对场景一（作业指导书）进行评分。
        """
        results = {}
        
        # 1. 结构完整性评分 (20分)
        logger.info("正在评估结构完整性...")
        structure_score = self._score_structure_completeness(document)
        results["structure_completeness"] = structure_score
        
        # 2. 内容完整性评分 (40分)
        logger.info("正在评估内容完整性...")
        content_score = self._score_content_completeness(document, extracted_info)
        results["content_completeness"] = content_score
        
        # 3. 语法规范性评分 (5分)
        logger.info("正在评估语法规范性...")
        grammar_score = self._score_grammar_accuracy(document)
        results["grammar_accuracy"] = grammar_score
        
        # 4. 整体评分
        logger.info("正在进行整体评分...")
        overall_score = self._score_overall(document, extracted_info, results)
        results["overall"] = overall_score
        
        # 计算总分和等级
        total_score = (
            structure_score.get("score", 0) + 
            content_score.get("score", 0) + 
            grammar_score.get("score", 0) +
            35  # 其他维度的基础分（暂时固定）
        )
        
        grade = self._calculate_grade(total_score)
        
        final_result = {
            "total_score": total_score,
            "grade": grade,
            "detailed_scores": results,
            "document_info": {
                "title": document.document_info.file_name,
                "scene_type": document.document_info.scene_type,
                "classification_confidence": document.document_info.classification_confidence
            }
        }
        
        logger.info(f"评分完成，总分: {total_score}, 等级: {grade}")
        return final_result

    def _score_structure_completeness(self, document: StandardizedDocument) -> Dict[str, Any]:
        """评估结构完整性。"""
        try:
            logger.info("🏗️ 正在为结构完整性评分提取专门内容...")
            
            # 使用专门的内容提取器获取结构相关内容
            structure_content = self.content_processor.extract_content_for_scoring_item(
                document, "structure"
            )
            
            logger.info(f"结构内容提取完成，长度: {len(structure_content)} 字符")
            
            # 提取章节列表用于prompt
            sections_found = []
            for text_item in document.text_content:
                if text_item.section_type == "title" and text_item.section_name:
                    sections_found.append(text_item.section_name)
            
            # 生成enhanced prompt，包含完整的结构信息
            prompt = self.scoring_prompts.get_structure_completeness_prompt(
                sections_found, self.required_sections_scenario_one
            )
            
            # 在prompt中添加完整的结构内容
            enhanced_prompt = f"""
{prompt}

以下是文档的完整结构信息：

{structure_content}

请基于以上完整的结构信息进行评分。
"""
            
            response = self.client.text_analysis(enhanced_prompt)
            
            # 解析响应
            from .info_extractor import LLMInfoExtractor  # 重用解析逻辑
            extractor = LLMInfoExtractor(self.client)
            parsed_result = extractor._parse_json_response(response)
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"结构完整性评分失败: {e}")
            return {
                "score": 0,
                "reasoning": "评分过程中发生错误",
                "error": str(e)
            }

    def _score_content_completeness(self, document: StandardizedDocument, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """评估内容完整性。"""
        try:
            logger.info("📝 正在为内容完整性评分提取专门内容...")
            
            # 使用专门的内容提取器获取内容完整性相关的内容
            content_data = self.content_processor.extract_content_for_scoring_item(
                document, "content"
            )
            
            logger.info(f"内容完整性数据提取完成，长度: {len(content_data)} 字符")
            
            technical_info = extracted_info.get("metadata", {})
            
            prompt = self.scoring_prompts.get_content_completeness_prompt(
                content_data, technical_info
            )
            
            response = self.client.text_analysis(prompt)
            
            # 解析响应
            from .info_extractor import LLMInfoExtractor
            extractor = LLMInfoExtractor(self.client)
            parsed_result = extractor._parse_json_response(response)
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"内容完整性评分失败: {e}")
            return {
                "score": 0,
                "reasoning": "评分过程中发生错误",
                "error": str(e)
            }

    def _score_grammar_accuracy(self, document: StandardizedDocument) -> Dict[str, Any]:
        """评估语法规范性。"""
        try:
            logger.info("📚 正在为语法规范性评分提取专门内容...")
            
            # 使用专门的内容提取器获取语法评估样本
            grammar_samples = self.content_processor.extract_content_for_scoring_item(
                document, "grammar"
            )
            
            logger.info(f"语法样本提取完成，长度: {len(grammar_samples)} 字符")
            
            prompt = self.scoring_prompts.get_grammar_errors_prompt(grammar_samples)
            response = self.client.text_analysis(prompt)
            
            # 解析响应
            from .info_extractor import LLMInfoExtractor
            extractor = LLMInfoExtractor(self.client)
            parsed_result = extractor._parse_json_response(response)
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"语法规范性评分失败: {e}")
            return {
                "score": 0,
                "reasoning": "评分过程中发生错误",
                "error": str(e)
            }

    def _score_overall(self, document: StandardizedDocument, extracted_info: Dict[str, Any], partial_results: Dict[str, Any]) -> Dict[str, Any]:
        """进行整体评分。"""
        try:
            document_summary = self._generate_content_summary(document, max_length=500)
            metadata = extracted_info.get("metadata", {})
            
            prompt = self.scoring_prompts.get_overall_scoring_prompt(
                document_summary, metadata
            )
            response = self.client.text_analysis(prompt)
            
            # 解析响应
            from .info_extractor import LLMInfoExtractor
            extractor = LLMInfoExtractor(self.client)
            parsed_result = extractor._parse_json_response(response)
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"整体评分失败: {e}")
            return {
                "total_score": 0,
                "reasoning": "评分过程中发生错误",
                "error": str(e)
            }

    def _score_unknown_scenario(self, document: StandardizedDocument, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """处理未知场景的评分。"""
        return {
            "error": "未知的文档场景类型",
            "scene_type": document.document_info.scene_type,
            "total_score": 0
        }

    def _generate_content_summary(self, document: StandardizedDocument, max_length: int = 1000) -> str:
        """生成文档内容摘要。"""
        summary_parts = []
        current_length = 0
        
        for text_item in document.text_content:
            if current_length >= max_length:
                break
            content = text_item.content
            if current_length + len(content) > max_length:
                # 截断到最大长度
                remaining = max_length - current_length
                content = content[:remaining] + "..."
            
            summary_parts.append(content)
            current_length += len(content)
        
        return "\n".join(summary_parts)

    def _calculate_grade(self, total_score: int) -> str:
        """根据总分计算等级。"""
        if total_score >= 90:
            return "优秀"
        elif total_score >= 80:
            return "良好"
        elif total_score >= 70:
            return "合格"
        else:
            return "不合格"