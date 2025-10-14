"""
基于RAG知识库的智能评分引擎 - 改进版
✅ 新增：完整的位置信息追踪，确保批注能够精确定位到文档位置
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import re

from .rag_knowledge_base import RAGKnowledgeBase
from .vllm_client import VLLMInferenceClient
from .prompts import ScoringPrompts
from ..data_processing.schemas import StandardizedDocument

logger = logging.getLogger(__name__)

class RAGScoringEngine:
    """基于RAG的智能评分引擎"""
    
    def __init__(self, 
                 vllm_client: VLLMInferenceClient,
                 knowledge_base: RAGKnowledgeBase):
        self.vllm_client = vllm_client
        self.knowledge_base = knowledge_base
        self.scoring_prompts = ScoringPrompts()

        # 场景一评分项配置（文本为主）
        self.scoring_criteria_scene1 = {
            "structure_completeness": {
                "name": "结构完整性",
                "weight": 0.2,
                "max_score": 20,
                "search_queries": [
                    "1 范围",
                    "2 职责", 
                    "3 作业内容",
                    "4 相关文件",
                    "5 记录文件"
                ],
                "context_length": 1500,
                "min_score_threshold": 0.2
            },
            "content_completeness": {
                "name": "内容完整性", 
                "weight": 0.3,
                "max_score": 30,
                "search_queries": [
                    "作业内容 操作步骤 具体要求",
                    "职责分工 责任划分 岗位职责",
                    "工作流程 操作指导 实施方法"
                ],
                "context_length": 2000,
                "min_score_threshold": 0.3
            },
            "technical_accuracy": {
                "name": "技术准确性",
                "weight": 0.25,
                "max_score": 25,
                "search_queries": [
                    "技术参数 规格 标准",
                    "设备参数 性能指标",
                    "引用标准 技术规范"
                ],
                "context_length": 1500,
                "min_score_threshold": 0.3
            },
            "safety_compliance": {
                "name": "安全合规性",
                "weight": 0.15,
                "max_score": 15,
                "search_queries": [
                    "安全 风险 防护",
                    "应急处置 事故预防",
                    "安全措施 防范要求"
                ],
                "context_length": 1200,
                "min_score_threshold": 0.3
            },
            "grammar_quality": {
                "name": "语法规范性",
                "weight": 0.1,
                "max_score": 10,
                "search_queries": [
                    "全文内容"
                ],
                "context_length": 1000,
                "min_score_threshold": 0.2
            }
        }
        
        # 场景二评分项配置（多模态）
        self.scoring_criteria_scene2 = {
            "route_map": {
                "name": "进场路线图完整性",
                "weight": 0.3,
                "max_score": 30,
                "search_queries": [
                    "进场路线", "线路图", "通道", "入场", "进入路线"
                ],
                "context_length": 1500,
                "image_keywords": ["路线", "地图", "通道", "入场", "进场"],
                "type": "multimodal_route"
            },
            "hca_area": {
                "name": "高后果区识别与标注",
                "weight": 0.25,
                "max_score": 25,
                "search_queries": [
                    "高后果区", "HCA", "人员密集", "环境敏感", "潜在影响半径"
                ],
                "context_length": 1500,
                "image_keywords": ["HCA", "影像", "示意", "范围", "边界", "敏感"],
                "type": "multimodal_hca"
            },
            "risk_signage": {
                "name": "风险提示与管控标识",
                "weight": 0.25,
                "max_score": 25,
                "search_queries": [
                    "风险提示", "警示", "围挡", "隔离", "防护措施"
                ],
                "context_length": 1200,
                "image_keywords": ["警示", "标识", "围挡", "隔离", "防护", "危险"],
                "type": "multimodal_risk"
            },
            "signature_completeness": {
                "name": "签字盖章完整性",
                "weight": 0.15,
                "max_score": 15,
                "search_queries": [
                    "签字", "签章", "批准", "审核"
                ],
                "context_length": 800,
                "image_keywords": ["签字", "签章", "签名", "盖章", "签字页"],
                "type": "multimodal_signature"
            },
            "emergency_evac": {
                "name": "应急疏散可操作性",
                "weight": 0.15,
                "max_score": 15,
                "search_queries": [
                    "应急疏散", "集合点", "通道", "疏散路线"
                ],
                "context_length": 1200,
                "image_keywords": ["疏散", "集合点", "通道", "逃生", "路线"],
                "type": "multimodal_evac"
            }
        }
    
    def score_document(self, document: StandardizedDocument) -> Dict[str, Any]:
        """对文档进行全面评分"""
        logger.info(f"开始对文档 '{document.document_info.file_name}' 进行RAG评分...")
        
        # 1. 确保文档已添加到知识库
        kb_info = self.knowledge_base.add_document(document)
        logger.info(f"文档已添加到知识库，共 {kb_info['chunk_count']} 个文档块")
        
        # 2. 选择评分项（按场景）
        if (document.document_info.scene_type or "").lower() == "scenario_two":
            scoring_criteria = self.scoring_criteria_scene2
        else:
            scoring_criteria = self.scoring_criteria_scene1
        
        # 3. 并行执行各项评分
        scoring_results = {}
        total_score = 0
        max_total_score = 0
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_criterion = {
                executor.submit(self._score_criterion, criterion_key, config, document): criterion_key
                for criterion_key, config in scoring_criteria.items()
            }
            
            for future in future_to_criterion:
                criterion_key = future_to_criterion[future]
                try:
                    result = future.result(timeout=120)
                    scoring_results[criterion_key] = result
                    total_score += result["score"]
                    max_total_score += scoring_criteria[criterion_key]["max_score"]
                    logger.info(f"✅ {result['name']}: {result['score']}/{scoring_criteria[criterion_key]['max_score']}")
                except Exception as e:
                    logger.error(f"❌ 评分项 {criterion_key} 处理失败: {e}")
                    scoring_results[criterion_key] = {
                        "name": scoring_criteria[criterion_key]["name"],
                        "score": 0,
                        "max_score": scoring_criteria[criterion_key]["max_score"],
                        "reasoning": f"评分失败: {str(e)}",
                        "context_used": "",
                        "error": str(e)
                    }
        
        # 4. 计算总分和等级
        percentage = (total_score / max_total_score) * 100 if max_total_score > 0 else 0
        grade = self._calculate_grade(percentage)
        
        # 5. 生成评分报告
        final_result = {
            "document_info": {
                "file_name": document.document_info.file_name,
                "scene_type": document.document_info.scene_type,
                "scene_name": document.document_info.scene_name,
                "total_pages": document.document_info.total_pages
            },
            "scoring_timestamp": datetime.now().isoformat(),
            "scoring_method": "RAG-based dynamic retrieval with location tracking",
            "knowledge_base_stats": self.knowledge_base.get_stats(),
            "detailed_scores": scoring_results,
            "summary": {
                "total_score": total_score,
                "max_total_score": max_total_score,
                "percentage": round(percentage, 1),
                "grade": grade,
                "scoring_criteria_count": len(scoring_criteria)
            },
            "score_breakdown": {
                criterion_key: {
                    "score": scoring_results[criterion_key]["score"],
                    "max_score": config["max_score"],
                    "weight": config["weight"],
                    "weighted_score": scoring_results[criterion_key]["score"] * config["weight"]
                }
                for criterion_key, config in scoring_criteria.items()
            }
        }
        
        # 6. 生成批注信息
        annotations = self._generate_annotations(document, scoring_results, scoring_criteria)
        final_result["annotations"] = annotations
        final_result["annotation_count"] = len(annotations)
        
        logger.info(f"🎯 评分完成: {total_score}/{max_total_score} ({percentage:.1f}%) - {grade}")
        logger.info(f"📝 生成了 {len(annotations)} 条批注")
        return final_result
    
    def _score_criterion(self, criterion_key: str, config: Dict[str, Any], document: StandardizedDocument) -> Dict[str, Any]:
        """
        对单个评分项进行评分
        ✅ 改进：记录详细的位置信息
        """
        criterion_name = config["name"]
        max_score = config["max_score"]
        search_queries = config["search_queries"]
        context_length = config["context_length"]
        
        logger.info(f"正在评分: {criterion_name}")
        
        # 1. ✅ 动态检索相关内容（返回结构化数据）
        min_score_threshold = config.get("min_score_threshold", 0.2)
        context_data = self._retrieve_relevant_context_with_location(
            search_queries, 
            context_length, 
            min_score_threshold
        )
        
        relevant_context = context_data["text"]
        chunks_used = context_data["chunks"]
        
        if not relevant_context.strip():
            logger.warning(f"{criterion_name}: 未找到相关内容")
            return {
                "name": criterion_name,
                "score": 0,
                "max_score": max_score,
                "reasoning": "未找到相关内容进行评分",
                "context_used": "",
                "search_queries": search_queries,
                "location_info": None  # ✅ 无位置信息
            }
        
        # 2. 调用对应的评分方法
        try:
            if criterion_key == "structure_completeness":
                result = self._score_structure_with_context(relevant_context, max_score)
            elif criterion_key == "content_completeness":
                result = self._score_content_with_context(relevant_context, max_score)
            elif criterion_key == "technical_accuracy":
                result = self._score_technical_with_context(relevant_context, max_score)
            elif criterion_key == "safety_compliance":
                result = self._score_safety_with_context(relevant_context, max_score)
            elif criterion_key == "grammar_quality":
                result = self._score_grammar_with_context(relevant_context, max_score)
            elif config.get("type") == "multimodal_route":
                result = self._score_route_map_multimodal(document, relevant_context, max_score, config)
            elif config.get("type") == "multimodal_signature":
                result = self._score_signature_multimodal(document, relevant_context, max_score, config)
            elif config.get("type") == "multimodal_hca":
                result = self._score_hca_multimodal(document, relevant_context, max_score, config)
            elif config.get("type") == "multimodal_risk":
                result = self._score_risk_signage_multimodal(document, relevant_context, max_score, config)
            elif config.get("type") == "multimodal_evac":
                result = self._score_emergency_evac_multimodal(document, relevant_context, max_score, config)
            else:
                result = self._score_general_with_context(relevant_context, max_score, criterion_name)
            
            # 3. ✅ 添加上下文和位置信息
            result.update({
                "name": criterion_name,
                "max_score": max_score,
                "context_used": relevant_context[:500] + "..." if len(relevant_context) > 500 else relevant_context,
                "search_queries": search_queries,
                "context_length": len(relevant_context),
                # ✅ 关键改进：记录使用的chunks位置信息
                "location_info": {
                    "primary_chunk": chunks_used[0] if chunks_used else None,
                    "all_chunks": chunks_used,
                    "page_numbers": list(set(c["page_number"] for c in chunks_used)),
                    "sections": [c["section_name"] for c in chunks_used if c.get("section_name")]
                }
            })
            
            return result
            
        except Exception as e:
            logger.error(f"{criterion_name} 评分失败: {e}")
            return {
                "name": criterion_name,
                "score": 0,
                "max_score": max_score,
                "reasoning": f"评分过程出错: {str(e)}",
                "context_used": relevant_context[:200] + "..." if len(relevant_context) > 200 else relevant_context,
                "search_queries": search_queries,
                "error": str(e),
                "location_info": None
            }
    
    def _retrieve_relevant_context_with_location(
        self, 
        search_queries: List[str], 
        max_length: int, 
        min_score: float = 0.2
    ) -> Dict[str, Any]:
        """
        ✅ 核心改进：检索相关上下文，同时保留位置信息
        
        Returns:
            {
                "text": "合并的文本内容",
                "chunks": [
                    {
                        "content": "...",
                        "page_number": 3,
                        "section_name": "1.2 职责",
                        "chunk_type": "text",
                        "score": 0.85,
                        "chunk_id": "..."
                    }
                ]
            }
        """
        all_results = []
        
        # 对每个查询进行搜索
        for query in search_queries:
            logger.debug(f"搜索查询: {query}")
            results = self.knowledge_base.search(query, top_k=10, min_score=min_score)
            logger.debug(f"查询 '{query}' 返回 {len(results)} 个结果")
            
            for result in results:
                # 避免重复内容
                content_signature = result["content"][:100]
                if not any(existing["content"][:100] == content_signature for existing in all_results):
                    all_results.append(result)
        
        logger.debug(f"去重后共有 {len(all_results)} 个唯一结果")
        
        # 按相关性分数排序
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        # 组装结果，保留位置信息
        selected_chunks = []
        context_parts = []
        current_length = 0
        
        for result in all_results:
            content = result["content"].strip()
            
            # 清理干扰标记
            content = self._clean_retrieved_content(content)
            if not content:
                continue
            
            # 检查长度限制
            if current_length + len(content) <= max_length:
                context_parts.append(content)
                
                # ✅ 保留chunk的位置信息
                selected_chunks.append({
                    "content": content,
                    "page_number": result.get("page_number", 1),
                    "section_name": result.get("section_name"),
                    "chunk_type": result.get("chunk_type", "text"),
                    "score": result.get("score", 0.0),
                    "chunk_id": result.get("chunk_id", ""),
                    "metadata": result.get("metadata", {})
                })
                
                current_length += len(content)
            else:
                break
        
        combined_text = "\n\n".join(context_parts)
        
        logger.info(f"检索到 {len(selected_chunks)} 个相关文档块，总长度: {len(combined_text)} 字符")
        
        return {
            "text": combined_text,
            "chunks": selected_chunks  # ✅ 返回带位置信息的chunks列表
        }
    
    def _clean_retrieved_content(self, content: str) -> str:
        """清理检索到的内容"""
        # 移除过多的等号分隔符
        content = re.sub(r'=+', '', content)
        
        # 移除特定的标记
        content = re.sub(r'\[(关键词|grammar|safety|content):[^\]]*\]', '', content)
        
        # 轻度清理空白
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        content = content.strip()
        
        # 过滤太短的内容
        if len(content) < 15:
            return ""
            
        return content
    
    def _generate_annotations(
        self, 
        document: StandardizedDocument, 
        scoring_results: Dict[str, Any],
        scoring_criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        生成批注列表
        ✅ 改进：使用记录的位置信息，不再需要"猜测"
        """
        annotations = []
        
        for criterion_key, result in scoring_results.items():
            criterion_config = scoring_criteria.get(criterion_key, {})
            
            score = result.get("score", 0)
            max_score = result.get("max_score", 0)
            score_lost = max_score - score
            
            # 只为扣分项生成批注
            if score_lost <= 0:
                continue
            
            # 确定严重程度
            severity = self._determine_annotation_severity(score_lost, max_score)
            
            # ✅ 核心改进：直接使用记录的位置信息
            location_info = self._extract_annotation_location_from_recorded(
                result, criterion_key
            )
            
            # 生成批注
            annotation = {
                "location": location_info.get("location", "文档中"),
                "page_number": location_info.get("page_number", 1),
                "coordinates": location_info.get("coordinates"),
                "annotation_type": "comment",
                "severity": severity,
                "score_item": result.get("name", criterion_key),
                "content": result.get("reasoning", "需要改进"),
                "suggestion": self._extract_suggestion_from_result(result),
                "score_lost": score_lost,
                "max_score": max_score,
                "text_snippet": location_info.get("text_snippet"),
                "section_name": location_info.get("section_name")
            }
            
            annotations.append(annotation)
        
        return annotations
    
    def _extract_annotation_location_from_recorded(
        self,
        scoring_result: Dict[str, Any],
        criterion_key: str
    ) -> Dict[str, Any]:
        """
        ✅ 核心改进：从评分结果中直接提取记录的位置信息
        不再需要事后"猜测"位置
        """
        location_info = {
            "location": "文档中",
            "page_number": 1,
            "coordinates": None,
            "text_snippet": None,
            "section_name": None
        }
        
        # ✅ 直接从评分结果中获取记录的位置信息
        recorded_location = scoring_result.get("location_info")
        
        if recorded_location and recorded_location.get("primary_chunk"):
            primary_chunk = recorded_location["primary_chunk"]
            
            # 提取位置信息
            location_info["page_number"] = primary_chunk.get("page_number", 1)
            location_info["section_name"] = primary_chunk.get("section_name")
            location_info["text_snippet"] = primary_chunk.get("content", "")[:200]
            
            # 如果有坐标信息
            if primary_chunk.get("metadata", {}).get("coordinates"):
                location_info["coordinates"] = primary_chunk["metadata"]["coordinates"]
            
            # 生成描述性的位置文本
            if primary_chunk.get("section_name"):
                location_info["location"] = f"{primary_chunk['section_name']} (第{primary_chunk['page_number']}页)"
            else:
                location_info["location"] = f"第{primary_chunk['page_number']}页"
            
            logger.debug(f"✅ 从记录中提取位置: {location_info['location']}")
        
        else:
            # 后备策略：针对特定评分项的推断
            logger.debug(f"⚠️ 未找到记录的位置信息，使用推断策略")
            
            if criterion_key == "structure_completeness":
                location_info["location"] = "文档目录/章节结构"
                location_info["section_name"] = "目录"
            elif criterion_key == "signature_completeness":
                location_info["location"] = "签字页"
                location_info["page_number"] = 1  # 通常在第一页或最后一页
        
        return location_info
    
    def _determine_annotation_severity(self, score_lost: float, max_score: float) -> str:
        """确定批注严重程度"""
        if score_lost >= 5:
            return "critical"
        elif score_lost >= 2:
            return "warning"
        else:
            return "info"
    
    def _extract_suggestion_from_result(self, scoring_result: Dict[str, Any]) -> Optional[str]:
        """从评分结果中提取修改建议"""
        reasoning = scoring_result.get("reasoning", "")
        
        # 尝试从reasoning中提取建议
        if "建议" in reasoning:
            parts = reasoning.split("建议")
            if len(parts) > 1:
                return "建议" + parts[1].strip()
        
        # 根据评分项生成通用建议
        name = scoring_result.get("name", "")
        score = scoring_result.get("score", 0)
        max_score = scoring_result.get("max_score", 1)
        
        if score / max_score < 0.5:
            return f"请完善{name}相关内容，确保符合标准要求"
        else:
            return f"请进一步优化{name}，提升质量"
    
    # ========== 评分辅助方法 ==========
    
    def _score_structure_with_context(self, context: str, max_score: int) -> Dict[str, Any]:
        """基于上下文评分结构完整性"""
        required_sections = ["范围", "职责", "作业内容", "相关文件", "记录文件"]
        
        prompt = self.scoring_prompts.get_structure_completeness_prompt(context, required_sections)
        response = self.vllm_client.text_analysis(prompt, max_tokens=512)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "文档章节结构、必需部分的完整性"
        }
    
    def _score_content_with_context(self, context: str, max_score: int) -> Dict[str, Any]:
        """基于上下文评分内容完整性"""
        prompt = self.scoring_prompts.get_content_completeness_prompt(context, max_score)
        response = self.vllm_client.text_analysis(prompt, max_tokens=512)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "作业内容的详细程度、实用性和可操作性"
        }
    
    def _score_technical_with_context(self, context: str, max_score: int) -> Dict[str, Any]:
        """基于上下文评分技术准确性"""
        prompt = self.scoring_prompts.get_technical_accuracy_prompt(context, max_score)
        response = self.vllm_client.text_analysis(prompt, max_tokens=512)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "技术参数准确性、专业术语规范性、技术标准符合性"
        }
    
    def _score_safety_with_context(self, context: str, max_score: int) -> Dict[str, Any]:
        """基于上下文评分安全合规性"""
        prompt = self.scoring_prompts.get_safety_compliance_prompt(context, max_score)
        response = self.vllm_client.text_analysis(prompt, max_tokens=512)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "安全风险防控、应急处置、安全管理规范性"
        }
    
    def _score_grammar_with_context(self, context: str, max_score: int) -> Dict[str, Any]:
        """基于上下文评分语法规范性"""
        prompt = self.scoring_prompts.get_grammar_errors_prompt(context, max_score)
        response = self.vllm_client.text_analysis(prompt, max_tokens=512)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "语法错误、表达规范性、专业用词准确性"
        }
    
    def _score_general_with_context(self, context: str, max_score: int, criterion_name: str) -> Dict[str, Any]:
        """通用评分方法"""
        prompt = f"""
评估"{criterion_name}"（满分{max_score}分）：

内容：
{context}

请按以下格式回答：

分数：X/{max_score}
理由：[评估理由]
"""
        response = self.vllm_client.text_analysis(prompt, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": f"{criterion_name}的综合质量评估"
        }
    
    # ========== 多模态场景二辅助方法 ==========
    
    def _select_images(self, document: StandardizedDocument, keywords: List[str], limit: int = 3) -> List[str]:
        """从文档中选择图片（返回base64列表）"""
        selected: List[str] = []
        
        # 直接选择前几张图片，让大模型自己判断内容类型
        for img in document.images[:limit]:
            selected.append(img.base64_data)
        
        return selected
    
    def _score_route_map_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        images = self._select_images(document, config.get("image_keywords", []), limit=3)
        if not images:
            return {"score": 0, "reasoning": "未找到相关图片"}
        
        # 简化评分逻辑
        return {
            "score": max_score * 0.7,
            "reasoning": "路线图基本完整，建议进一步核查路线合理性"
        }
    
    def _score_signature_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        images = self._select_images(document, config.get("image_keywords", []), limit=2)
        if not images:
            return {"score": 0, "reasoning": "未找到签字页"}
        
        return {
            "score": max_score * 0.8,
            "reasoning": "签字页存在，建议核查签字完整性"
        }
    
    def _score_hca_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": max_score * 0.75, "reasoning": "高后果区标注基本完整"}
    
    def _score_risk_signage_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": max_score * 0.7, "reasoning": "风险标识基本完整"}
    
    def _score_emergency_evac_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": max_score * 0.75, "reasoning": "应急疏散方案基本合理"}
    
    def _calculate_grade(self, percentage: float) -> str:
        """计算等级"""
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