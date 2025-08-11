"""
基于RAG知识库的智能评分引擎
动态检索相关内容，为每个评分项生成针对性的上下文
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import time

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
        
        # 评分项配置 - 更细化的评分维度
        self.scoring_criteria = {
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
                    "表头 管径 材质 壁厚",
                    "1016 X70 操作压力",
                    "813 X60 允许悬空",
                    "技术规范 设计 标准",
                    "MPa 管线名称 长度"
                ],
                "context_length": 1800,
                "min_score_threshold": 0.2
            },
            "safety_compliance": {
                "name": "安全合规性",
                "weight": 0.15,
                "max_score": 15,
                "search_queries": [
                    "安全要求 风险控制 应急处置",
                    "防护措施 安全隐患 风险识别",
                    "应急预案 安全管理 防范措施 汛情"
                ],
                "context_length": 1500,
                "min_score_threshold": 0.25
            },
            "grammar_quality": {
                "name": "语法规范性",
                "weight": 0.1,
                "max_score": 10,
                "search_queries": [
                    "第1页 第2页 第3页",
                    "内容 文字 描述 表达",
                    "管道 汛期 防汛"  # 获取有实际内容的文本样本
                ],
                "context_length": 1200,
                "min_score_threshold": 0.2
            }
        }
    
    def score_document(self, document: StandardizedDocument) -> Dict[str, Any]:
        """对文档进行全面评分"""
        logger.info(f"开始对文档 '{document.document_info.file_name}' 进行RAG评分...")
        
        # 1. 确保文档已添加到知识库
        kb_info = self.knowledge_base.add_document(document)
        logger.info(f"文档已添加到知识库，共 {kb_info['chunk_count']} 个文档块")
        
        # 2. 并行执行各项评分
        scoring_results = {}
        total_score = 0
        max_total_score = 0
        
        # 使用线程池并行处理评分
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_criterion = {
                executor.submit(self._score_criterion, criterion_key, config, document): criterion_key
                for criterion_key, config in self.scoring_criteria.items()
            }
            
            for future in future_to_criterion:
                criterion_key = future_to_criterion[future]
                try:
                    result = future.result(timeout=120)  # 2分钟超时
                    scoring_results[criterion_key] = result
                    total_score += result["score"]
                    max_total_score += self.scoring_criteria[criterion_key]["max_score"]
                    logger.info(f"✅ {result['name']}: {result['score']}/{self.scoring_criteria[criterion_key]['max_score']}")
                except Exception as e:
                    logger.error(f"❌ 评分项 {criterion_key} 处理失败: {e}")
                    scoring_results[criterion_key] = {
                        "name": self.scoring_criteria[criterion_key]["name"],
                        "score": 0,
                        "max_score": self.scoring_criteria[criterion_key]["max_score"],
                        "reasoning": f"评分失败: {str(e)}",
                        "context_used": "",
                        "error": str(e)
                    }
        
        # 3. 计算总分和等级
        percentage = (total_score / max_total_score) * 100 if max_total_score > 0 else 0
        grade = self._calculate_grade(percentage)
        
        # 4. 生成评分报告
        final_result = {
            "document_info": {
                "file_name": document.document_info.file_name,
                "scene_type": document.document_info.scene_type,
                "scene_name": document.document_info.scene_name,
                "total_pages": document.document_info.total_pages
            },
            "scoring_timestamp": datetime.now().isoformat(),
            "scoring_method": "RAG-based dynamic retrieval",
            "knowledge_base_stats": self.knowledge_base.get_stats(),
            "detailed_scores": scoring_results,
            "summary": {
                "total_score": total_score,
                "max_total_score": max_total_score,
                "percentage": round(percentage, 1),
                "grade": grade,
                "scoring_criteria_count": len(self.scoring_criteria)
            },
            "score_breakdown": {
                criterion_key: {
                    "score": scoring_results[criterion_key]["score"],
                    "max_score": config["max_score"],
                    "weight": config["weight"],
                    "weighted_score": scoring_results[criterion_key]["score"] * config["weight"]
                }
                for criterion_key, config in self.scoring_criteria.items()
            }
        }
        
        logger.info(f"🎯 评分完成: {total_score}/{max_total_score} ({percentage:.1f}%) - {grade}")
        return final_result
    
    def _score_criterion(self, criterion_key: str, config: Dict[str, Any], document: StandardizedDocument) -> Dict[str, Any]:
        """对单个评分项进行评分"""
        criterion_name = config["name"]
        max_score = config["max_score"]
        search_queries = config["search_queries"]
        context_length = config["context_length"]
        
        logger.info(f"正在评分: {criterion_name}")
        
        # 1. 动态检索相关内容
        min_score_threshold = config.get("min_score_threshold", 0.2)
        relevant_context = self._retrieve_relevant_context(search_queries, context_length, min_score_threshold)
        
        if not relevant_context.strip():
            logger.warning(f"{criterion_name}: 未找到相关内容")
            return {
                "name": criterion_name,
                "score": 0,
                "max_score": max_score,
                "reasoning": "未找到相关内容进行评分",
                "context_used": "",
                "search_queries": search_queries
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
            else:
                result = self._score_general_with_context(relevant_context, max_score, criterion_name)
            
            # 3. 添加上下文信息
            result.update({
                "name": criterion_name,
                "max_score": max_score,
                "context_used": relevant_context[:500] + "..." if len(relevant_context) > 500 else relevant_context,
                "search_queries": search_queries,
                "context_length": len(relevant_context)
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
                "error": str(e)
            }
    
    def _retrieve_relevant_context(self, search_queries: List[str], max_length: int, min_score: float = 0.2) -> str:
        """检索相关上下文"""
        all_results = []
        
        # 对每个查询进行搜索
        for query in search_queries:
            logger.debug(f"搜索查询: {query}")
            results = self.knowledge_base.search(query, top_k=10, min_score=min_score)
            logger.debug(f"查询 '{query}' 返回 {len(results)} 个结果")
            
            for result in results:
                # 避免重复内容 - 使用内容的前100字符作为唯一标识
                content_signature = result["content"][:100]
                if not any(existing["content"][:100] == content_signature for existing in all_results):
                    all_results.append(result)
        
        logger.debug(f"去重后共有 {len(all_results)} 个唯一结果")
        
        # 按相关性分数排序
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        # 优化格式 - 更好的内容清理和组织
        context_parts = []
        current_length = 0
        
        for result in all_results:
            content = result["content"].strip()
            
            # 清理干扰标记
            content = self._clean_retrieved_content(content)
            if not content:  # 清理后如果为空，跳过
                continue
                
            # 检查长度限制
            if current_length + len(content) + 2 <= max_length:  # +2 for \n\n
                context_parts.append(content)
                current_length += len(content) + 2
            else:
                # 如果还有剩余空间，尝试添加部分内容
                remaining_space = max_length - current_length - 5
                if remaining_space > 100:  # 至少100字符才有意义
                    partial_content = content[:remaining_space] + "..."
                    context_parts.append(partial_content)
                break
        
        context = "\n\n".join(context_parts)
        logger.info(f"检索到上下文长度: {len(context)} 字符，包含 {len(context_parts)} 个片段")
        return context
    
    def _clean_retrieved_content(self, content: str) -> str:
        """清理检索到的内容 - 保留重要的结构信息"""
        import re
        
        # 检查是否是重要的章节标题（如 "1 范围", "2 职责" 等）
        if re.match(r'^\d+\s+[范围职责作业内容相关文件记录文件]', content.strip()):
            return content.strip()  # 保留章节标题，不进行过滤
        
        # 只移除明显的干扰标记，保留重要的章节信息
        # 移除分隔符但保留章节标题  
        content = re.sub(r'=== .* ===', '', content)
        
        # 移除特定的标记
        content = re.sub(r'\[(关键词|grammar|safety|content):[^\]]*\]', '', content)
        
        # 轻度清理空白，保留换行结构
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # 合并多个空行为两个
        content = re.sub(r'[ \t]+', ' ', content)  # 合并空格和tab
        
        # 清理首尾空白
        content = content.strip()
        
        # 过滤太短的内容，但保留章节标题
        if len(content) < 15:
            return ""
            
        return content
    
    def _score_structure_with_context(self, context: str, max_score: int) -> Dict[str, Any]:
        """基于上下文评分结构完整性"""
        required_sections = ["范围", "职责", "作业内容", "相关文件", "记录文件"]
        
        prompt = self.scoring_prompts.get_structure_completeness_prompt(context, required_sections)
        response = self.vllm_client.text_analysis(prompt, max_tokens=512)
        
        # 使用新的简化解析方法
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
    
    # 旧的解析方法已被简化的parse_simple_response替代
    
    def _calculate_grade(self, percentage: float) -> str:
        """根据百分比计算等级"""
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
    
    def search_document_content(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """直接通过知识库实例搜索文档内容"""
        return self.knowledge_base.search(query, top_k=top_k, min_score=0.2) 