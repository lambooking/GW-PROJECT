"""
基于RAG知识库的智能评分引擎
动态检索相关内容，为每个评分项生成针对性的上下文
"""
import json
import logging
import sys
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import time
from pathlib import Path

from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
from src.inference.rag_knowledge_base import RAGKnowledgeBase
from src.inference.rag_scoring_engine import RAGScoringEngine
from src.inference.vllm_client import VLLMInferenceClient
from src.inference.prompts import ScoringPrompts
from src.data_processing.schemas import StandardizedDocument

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
                    "文档章节结构 目录 标题 编号",
                    "范围 职责 作业内容 相关文件 记录文件",
                    "文档组织结构 章节层次"
                ],
                "context_length": 1500
            },
            "content_completeness": {
                "name": "内容完整性", 
                "weight": 0.3,
                "max_score": 30,
                "search_queries": [
                    "作业内容 操作步骤 具体要求",
                    "职责分工 责任划分",
                    "工作流程 操作指导 实施方法"
                ],
                "context_length": 2000
            },
            "technical_accuracy": {
                "name": "技术准确性",
                "weight": 0.25,
                "max_score": 25,
                "search_queries": [
                    "技术参数 规格指标 标准数据",
                    "技术规范 设计要求 技术标准",
                    "工程技术 施工要求 质量标准"
                ],
                "context_length": 1800
            },
            "safety_compliance": {
                "name": "安全合规性",
                "weight": 0.15,
                "max_score": 15,
                "search_queries": [
                    "安全要求 风险控制 应急处置",
                    "防护措施 安全隐患 风险识别",
                    "应急预案 安全管理 防范措施"
                ],
                "context_length": 1500
            },
            "grammar_quality": {
                "name": "语法规范性",
                "weight": 0.1,
                "max_score": 10,
                "search_queries": [
                    "第1页 第2页 第3页 文档格式",  # 获取样本文本
                    "语言表达 文字描述",
                    "专业术语 表达方式"
                ],
                "context_length": 1000
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
        relevant_context = self._retrieve_relevant_context(search_queries, context_length)
        
        if not relevant_context.strip():
            logger.warning(f"{criterion_name}: 未找到相关内容")
            return {
                "name": criterion_name,
                "score": 0,
                "max_score": max_score,
                "reasoning": "未找到相关内容进行评分",
                "context_used": "",
                "search_queries": search_queries,
                "evaluation_focus": "综合评估"
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
    
    def _retrieve_relevant_context(self, search_queries: List[str], max_length: int) -> str:
        """检索相关上下文"""
        all_results = []
        
        # 对每个查询进行搜索
        for query in search_queries:
            results = self.knowledge_base.search(query, top_k=8, min_score=0.2)
            for result in results:
                # 避免重复内容
                if not any(result["content"] == existing["content"] for existing in all_results):
                    all_results.append(result)
        
        # 按相关性分数排序
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        # 组装上下文
        context_parts = []
        current_length = 0
        
        for result in all_results:
            content = result["content"]
            page_info = f"[第{result['page_number']}页]"
            
            if result["section_name"]:
                section_info = f"[{result['section_name']}]"
                full_content = f"{page_info}{section_info} {content}"
            else:
                full_content = f"{page_info} {content}"
            
            if current_length + len(full_content) <= max_length:
                context_parts.append(full_content)
                current_length += len(full_content)
            else:
                # 如果还有空间，尝试添加部分内容
                remaining_space = max_length - current_length
                if remaining_space > 100:  # 至少100字符才有意义
                    partial_content = full_content[:remaining_space] + "..."
                    context_parts.append(partial_content)
                break
        
        context = "\n\n".join(context_parts)
        logger.debug(f"检索到上下文长度: {len(context)} 字符，包含 {len(context_parts)} 个片段")
        return context
    
    def _score_structure_with_context(self, context: str, max_score: int) -> Dict[str, Any]:
        """基于上下文评分结构完整性"""
        required_sections = ["范围", "职责", "作业内容", "相关文件", "记录文件"]
        
        prompt = self.scoring_prompts.get_structure_completeness_prompt(context, required_sections)
        response = self.vllm_client.text_analysis(prompt)
        
        # 解析响应并计算分数
        score, reasoning = self._parse_scoring_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "文档章节结构、必需部分的完整性"
        }
    
    def _score_content_with_context(self, context: str, max_score: int) -> Dict[str, Any]:
        """基于上下文评分内容完整性"""
        prompt = self.scoring_prompts.get_content_completeness_prompt(context)
        response = self.vllm_client.text_analysis(prompt)
        
        score, reasoning = self._parse_scoring_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "作业内容的详细程度、实用性和可操作性"
        }
    
    def _score_technical_with_context(self, context: str, max_score: int) -> Dict[str, Any]:
        """基于上下文评分技术准确性"""
        prompt = f"""
请根据以下技术内容，评估技术准确性和专业水平：

{context}

评分标准（满分{max_score}分）：
1. 技术参数是否准确、具体
2. 技术标准和规范引用是否正确
3. 专业术语使用是否规范
4. 技术要求是否明确可执行
5. 是否符合行业技术标准

请给出具体分数和详细理由。
"""
        response = self.vllm_client.text_analysis(prompt)
        score, reasoning = self._parse_scoring_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "技术参数准确性、专业术语规范性、技术标准符合性"
        }
    
    def _score_safety_with_context(self, context: str, max_score: int) -> Dict[str, Any]:
        """基于上下文评分安全合规性"""
        prompt = f"""
请根据以下安全相关内容，评估安全合规性：

{context}

评分标准（满分{max_score}分）：
1. 安全风险识别是否全面
2. 防护措施是否具体有效
3. 应急处置流程是否清晰
4. 安全责任是否明确
5. 是否符合安全管理要求

请给出具体分数和详细理由。
"""
        response = self.vllm_client.text_analysis(prompt)
        score, reasoning = self._parse_scoring_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "安全风险防控、应急处置、安全管理规范性"
        }
    
    def _score_grammar_with_context(self, context: str, max_score: int) -> Dict[str, Any]:
        """基于上下文评分语法规范性"""
        prompt = self.scoring_prompts.get_grammar_errors_prompt(context)
        response = self.vllm_client.text_analysis(prompt)
        
        score, reasoning = self._parse_scoring_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "语法错误、表达规范性、专业用词准确性"
        }
    
    def _score_general_with_context(self, context: str, max_score: int, criterion_name: str) -> Dict[str, Any]:
        """通用评分方法"""
        prompt = f"""
请根据以下内容，对"{criterion_name}"进行评分：

{context}

评分标准（满分{max_score}分）：
请根据内容质量、完整性、专业性等方面进行综合评估。

请给出具体分数和详细理由。
"""
        response = self.vllm_client.text_analysis(prompt)
        score, reasoning = self._parse_scoring_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": f"{criterion_name}的综合质量评估"
        }
    
    def _parse_scoring_response(self, response: str, max_score: int) -> tuple[int, str]:
        """解析评分响应"""
        try:
            # 尝试从响应中提取分数
            lines = response.strip().split('\n')
            score = 0
            reasoning = response
            
            for line in lines:
                # 查找包含分数的行
                if '分' in line and any(char.isdigit() for char in line):
                    # 提取数字
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        potential_score = int(numbers[0])
                        if 0 <= potential_score <= max_score:
                            score = potential_score
                            break
            
            # 如果没有找到有效分数，使用启发式方法
            if score == 0:
                if '优秀' in response or '很好' in response or '完整' in response:
                    score = max(int(max_score * 0.8), 1)
                elif '良好' in response or '较好' in response:
                    score = max(int(max_score * 0.6), 1)
                elif '一般' in response or '基本' in response:
                    score = max(int(max_score * 0.4), 1)
                elif '较差' in response or '不足' in response:
                    score = max(int(max_score * 0.2), 0)
                else:
                    score = max(int(max_score * 0.5), 1)  # 默认中等分数
            
            return score, reasoning
            
        except Exception as e:
            logger.error(f"解析评分响应失败: {e}")
            return max(int(max_score * 0.5), 1), f"解析失败，给予默认分数。原始响应: {response[:200]}..."
    
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
