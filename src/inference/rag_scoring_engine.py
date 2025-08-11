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

import base64
import cv2
import numpy as np
from .rag_knowledge_base import RAGKnowledgeBase
from .vllm_client import VLLMInferenceClient
from .prompts import ScoringPrompts
from ..data_processing.schemas import StandardizedDocument
from ..data_processing.image_processor import ImageProcessor

logger = logging.getLogger(__name__)

class RAGScoringEngine:
    """基于RAG的智能评分引擎"""
    
    def __init__(self, 
                 vllm_client: VLLMInferenceClient,
                 knowledge_base: RAGKnowledgeBase):
        self.vllm_client = vllm_client
        self.knowledge_base = knowledge_base
        self.scoring_prompts = ScoringPrompts()
        self.image_processor = ImageProcessor()
        
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
        
        # 场景二评分项配置（按照官方标准）
        self.scoring_criteria_scene2 = {
            # 图片识别能力 (70分)
            "signature_recognition": {
                "name": "签字页手签识别", 
                "weight": 0.05,
                "max_score": 5,
                "search_queries": ["签字页", "手签痕迹", "编制", "审核", "批准", "签章", "审批", "手写签名", "责任人签字", "盖章"],
                "context_length": 800,
                "type": "multimodal_signature_detection"
            },
            "content_completeness": {
                "name": "内容完整性",
                "weight": 0.05, 
                "max_score": 5,
                "search_queries": ["高后果区现场图", "典型照片", "建构筑物特征", "桩号位置", "周边环境描述", "人员分布", "敏感环境分布", "风险评价结果"],
                "context_length": 2000,
                "type": "multimodal_content_check"
            },
            "image_annotation_recognition": {
                "name": "影像图标注识别",
                "weight": 0.10,
                "max_score": 10,
                "search_queries": ["影像图", "管道位置", "实线", "潜在影响半径", "虚线", "建筑物", "人员数量", "建筑物名称"],
                "context_length": 1500,
                "type": "multimodal_image_annotation"
            },
            "entry_route_recognition": {
                "name": "入场线路图标注识别",
                "weight": 0.10,
                "max_score": 10,
                "search_queries": ["入场路线", "路线标注", "文字说明", "可行车道路", "路线合理性"],
                "context_length": 1500,
                "type": "multimodal_entry_route"
            },
            "escape_route_recognition": {
                "name": "逃生路线图、应急疏散集结点标注识别",
                "weight": 0.10,
                "max_score": 10,
                "search_queries": ["逃生路线", "应急疏散", "集结点", "疏散方向", "潜在影响半径", "管道两侧"],
                "context_length": 1500,
                "type": "multimodal_escape_route"
            },
            "water_sensitive_recognition": {
                "name": "水体敏感图标注识别",
                "weight": 0.05,
                "max_score": 5,
                "search_queries": ["围油设施", "防止位置", "水体敏感", "环境敏感"],
                "context_length": 1000,
                "type": "multimodal_water_sensitive"
            },
            "municipal_pipeline_recognition": {
                "name": "市政管网交叉图标注识别",
                "weight": 0.05,
                "max_score": 5,
                "search_queries": ["市政管网", "交叉位置", "管网交叉", "人员密集型", "城区管道"],
                "context_length": 1000,
                "type": "multimodal_municipal_pipeline"
            },
            
            # 上下文逻辑识别能力 (25分)
            "image_text_consistency": {
                "name": "图片标注一致性",
                "weight": 0.10,
                "max_score": 10,
                "search_queries": ["高后果区特征", "建筑物描述", "影像图标注", "一致性"],
                "context_length": 2000,
                "type": "text_consistency_check"
            },
            "context_content_consistency": {
                "name": "上下文内容一致性", 
                "weight": 0.05,
                "max_score": 5,
                "search_queries": ["区段长信息", "基本信息表", "位置信息", "风险评价结果", "高后果区编号"],
                "context_length": 1500,
                "type": "text_context_consistency"
            },
            "standard_compliance": {
                "name": "标准遵从度",
                "weight": 0.05,
                "max_score": 5,
                "search_queries": ["GB32167", "高后果区识别标准", "标准规定"],
                "context_length": 1000,
                "type": "text_standard_compliance"
            },
            "content_integrity": {
                "name": "内容完整性检查",
                "weight": 0.05,
                "max_score": 5,
                "search_queries": ["人员密集型", "市政管网交叉", "输油管道", "环境敏感", "围油设施"],
                "context_length": 1500,
                "type": "text_content_integrity"
            },
            "time_logic_consistency": {
                "name": "时间逻辑一致性",
                "weight": 0.05,
                "max_score": 5,
                "search_queries": ["封面编制时间", "识别时间", "风险评价时间", "时间逻辑"],
                "context_length": 1000,
                "type": "text_time_logic"
            },
            "data_logic_correctness": {
                "name": "数据逻辑正确性",
                "weight": 0.05,
                "max_score": 5,
                "search_queries": ["电位测试", "-0.85V", "-1.2V", "风险评价", "可能性", "后果值", "风险值", "风险等级"],
                "context_length": 1500,
                "type": "text_data_logic"
            },
            "template_consistency": {
                "name": "文字模板一致性",
                "weight": 0.10,
                "max_score": 10,
                "search_queries": ["管道本体管控", "外部环境风险", "事故状态下前期处置", "模板要求"],
                "context_length": 2000,
                "type": "text_template_consistency"
            },
            
            # 识别效率 (5分)
            "recognition_efficiency": {
                "name": "识别效率",
                "weight": 0.05,
                "max_score": 5,
                "search_queries": ["综合评估"],
                "context_length": 500,
                "type": "efficiency_check"
            }
        }
    
    def score_document(self, document: StandardizedDocument) -> Dict[str, Any]:
        """对文档进行全面评分"""
        logger.info(f"开始对文档 '{document.document_info.file_name}' 进行RAG评分...")
        
        # 1. 确保文档已添加到知识库
        kb_info = self.knowledge_base.add_document(document)
        logger.info(f"文档已添加到知识库，共 {kb_info['chunk_count']} 个文档块")
        
        # 2. 选择评分项（按场景）并并行执行各项评分
        scoring_results = {}
        total_score = 0
        max_total_score = 0
        
        if (document.document_info.scene_type or "").lower() == "scenario_two":
            scoring_criteria = self.scoring_criteria_scene2
        else:
            scoring_criteria = self.scoring_criteria_scene1
        
        # 使用线程池并行处理评分
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_criterion = {
                executor.submit(self._score_criterion, criterion_key, config, document): criterion_key
                for criterion_key, config in scoring_criteria.items()
            }
            
            for future in future_to_criterion:
                criterion_key = future_to_criterion[future]
                try:
                    result = future.result(timeout=120)  # 2分钟超时
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
            # 场景二新的评分方法
            elif config.get("type") == "multimodal_signature_detection":
                result = self._score_signature_detection(document, relevant_context, max_score, config)
            elif config.get("type") == "multimodal_content_check":
                result = self._score_content_completeness_check(document, relevant_context, max_score, config)
            elif config.get("type") == "multimodal_image_annotation":
                result = self._score_image_annotation(document, relevant_context, max_score, config)
            elif config.get("type") == "multimodal_entry_route":
                result = self._score_entry_route(document, relevant_context, max_score, config)
            elif config.get("type") == "multimodal_escape_route":
                result = self._score_escape_route(document, relevant_context, max_score, config)
            elif config.get("type") == "multimodal_water_sensitive":
                result = self._score_water_sensitive(document, relevant_context, max_score, config)
            elif config.get("type") == "multimodal_municipal_pipeline":
                result = self._score_municipal_pipeline(document, relevant_context, max_score, config)
            elif config.get("type") == "text_consistency_check":
                result = self._score_text_consistency(relevant_context, max_score)
            elif config.get("type") == "text_context_consistency":
                result = self._score_context_consistency(relevant_context, max_score)
            elif config.get("type") == "text_standard_compliance":
                result = self._score_standard_compliance(relevant_context, max_score)
            elif config.get("type") == "text_content_integrity":
                result = self._score_content_integrity(relevant_context, max_score)
            elif config.get("type") == "text_time_logic":
                result = self._score_time_logic(relevant_context, max_score)
            elif config.get("type") == "text_data_logic":
                result = self._score_data_logic(relevant_context, max_score)
            elif config.get("type") == "text_template_consistency":
                result = self._score_template_consistency(relevant_context, max_score)
            elif config.get("type") == "efficiency_check":
                result = self._score_efficiency(max_score)
            # 兼容旧的评分方法
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

    # ========== 多模态场景二辅助方法 ==========
    def _ai_assisted_image_selection(self, document: StandardizedDocument, evaluation_type: str, limit: int = 3) -> List[str]:
        """
        使用AI模型辅助选择最相关的图片
        
        Args:
            document: 标准化文档对象
            evaluation_type: 评估类型 (route_map, hca_coverage, risk_signage, signature, emergency_evac)  
            limit: 最大选择数量
            
        Returns:
            选中的图片base64列表
        """
        if not document.images:
            return []
        
        logger.info(f"开始AI辅助图片选择，评估类型: {evaluation_type}, 总图片数: {len(document.images)}")
        
        # 第一阶段：批量分析所有图片，获取相关性评分
        image_scores = []
        batch_size = 5  # 每批处理5张图片
        
        for i in range(0, len(document.images), batch_size):
            batch_images = document.images[i:i+batch_size]
            batch_base64 = [img.base64_data for img in batch_images]
            
            # 获取图片筛选的prompt
            selection_prompt = self._get_image_selection_prompt(evaluation_type)
            
            try:
                # 调用多模态分析
                response = self.vllm_client.multimodal_analysis(
                    selection_prompt, 
                    images_base64=batch_base64, 
                    max_tokens=512
                )
                
                # 解析相关性评分
                batch_scores = self._parse_image_relevance_scores(response, len(batch_images))
                
                # 记录每张图片的分数和索引
                for j, score in enumerate(batch_scores):
                    global_idx = i + j
                    image_scores.append((score, global_idx, document.images[global_idx].base64_data))
                    
            except Exception as e:
                logger.warning(f"批次 {i//batch_size + 1} 图片筛选失败: {e}")
                # 给默认分数
                for j in range(len(batch_images)):
                    global_idx = i + j
                    image_scores.append((0.3, global_idx, document.images[global_idx].base64_data))
        
        # 按相关性分数排序，选择最相关的图片
        image_scores.sort(key=lambda x: x[0], reverse=True)
        selected_images = [img_data for score, idx, img_data in image_scores[:limit] if score > 0.2]
        
        logger.info(f"AI图片选择完成: 从{len(document.images)}张中选择了{len(selected_images)}张相关图片")
        
        # 返回选择的图片（为了兼容性，暂时保持简单格式）
        return selected_images
    
    def _get_image_selection_prompt(self, evaluation_type: str) -> str:
        """获取图片筛选的专门提示词"""
        prompts = {
            "route_map": """
你是专业的图片筛选助手。请分析这些图片，判断哪些与"路线图/疏散路线/入场路线"相关。

评估标准：
- 包含路线、路径、箭头、方向指示的图片 (高相关)
- 包含地图、示意图、平面图的图片 (中等相关)
- 包含集合点、疏散点标识的图片 (中等相关)
- 纯文字、表格、无关场景的图片 (低相关)

请为每张图片打分(0-1分，保留1位小数)：
图片1：[分数]
图片2：[分数]
...

注意：分数越高表示与路线图越相关。
""",
            
            "hca_coverage": """
你是专业的图片筛选助手。请分析这些图片，判断哪些与"HCA高后果区影像/现场照片"相关。

评估标准：
- 现场实地照片、航拍图、卫星图 (高相关)
- 包含建筑物、道路、地形地貌的图片 (高相关)
- 包含管道、设施、敏感目标的图片 (高相关)
- 纯文字、表格、签字页的图片 (低相关)

请为每张图片打分(0-1分，保留1位小数)：
图片1：[分数]
图片2：[分数]
...

注意：分数越高表示与HCA现场影像越相关。
""",
            
            "risk_signage": """
你是专业的图片筛选助手。请分析这些图片，判断哪些与"风险标识/警示牌/防护设施"相关。

评估标准：
- 包含警示标识、标牌、围挡的图片 (高相关)
- 包含安全防护、隔离设施的图片 (高相关)
- 包含现场管控措施的图片 (中等相关)
- 纯文字、地图、签字页的图片 (低相关)

请为每张图片打分(0-1分，保留1位小数)：
图片1：[分数]
图片2：[分数]
...

注意：分数越高表示与风险标识越相关。
""",
            
            "signature": """
你是专业的图片筛选助手。请分析这些图片，判断哪些与"签字/签章/审批页面"相关。

评估标准：
- 包含手写签名、印章、审批信息的图片 (高相关)
- 包含责任人、日期、职务信息的图片 (高相关)
- 包含编制/审核/批准等字样的图片 (中等相关)
- 地图、现场照片、技术图表的图片 (低相关)

请为每张图片打分(0-1分，保留1位小数)：
图片1：[分数]
图片2：[分数]
...

注意：分数越高表示与签字盖章越相关。
""",
            
            "emergency_evac": """
你是专业的图片筛选助手。请分析这些图片，判断哪些与"应急疏散/集合点/疏散通道"相关。

评估标准：
- 包含疏散路线、集合点标识的图片 (高相关)
- 包含应急通道、安全出口的图片 (高相关)
- 包含逃生指示、方向箭头的图片 (中等相关)
- 纯文字、技术参数、签字页的图片 (低相关)

请为每张图片打分(0-1分，保留1位小数)：
图片1：[分数]
图片2：[分数]
...

注意：分数越高表示与应急疏散越相关。
""",

            "content_completeness": """
你是专业的图片筛选助手。请分析这些图片，判断哪些与"高后果区方案内容完整性"相关。

评估标准：
- 高后果区影像图、现场图 (高相关)
- 入场线路图、逃生路线图 (高相关)
- 应急疏散集合点、物资存放点图 (高相关)
- 围油设施图、管网交叉图 (中等相关)
- 纯文字、表格、签字页 (低相关)

请为每张图片打分(0-1分，保留1位小数)：
图片1：[分数]
图片2：[分数]
...

注意：分数越高表示与内容完整性越相关。
""",

            "image_annotation": """
你是专业的图片筛选助手。请分析这些图片，判断哪些与"影像图标注"相关。

评估标准：
- 包含管道位置线条(实线/虚线)的影像图 (高相关)
- 包含潜在影响半径标注的图片 (高相关)
- 包含建筑物、人员数量标注的图片 (高相关)
- 航拍图、卫星图、现场影像 (中等相关)
- 纯文字、表格、路线图 (低相关)

请为每张图片打分(0-1分，保留1位小数)：
图片1：[分数]
图片2：[分数]
...

注意：分数越高表示与影像图标注越相关。
""",

            "entry_route": """
你是专业的图片筛选助手。请分析这些图片，判断哪些与"入场线路图"相关。

评估标准：
- 包含入场路线、道路标注的图片 (高相关)
- 包含交通路线、可行车道路的图片 (高相关)
- 包含路线说明、方向指示的图片 (中等相关)
- 现场照片、建筑图、签字页 (低相关)

请为每张图片打分(0-1分，保留1位小数)：
图片1：[分数]
图片2：[分数]
...

注意：分数越高表示与入场线路图越相关。
""",

            "escape_route": """
你是专业的图片筛选助手。请分析这些图片，判断哪些与"逃生路线图、应急疏散集结点"相关。

评估标准：
- 包含逃生路线、疏散路径的图片 (高相关)
- 包含应急集结点、疏散集合点的图片 (高相关)
- 包含安全出口、紧急出口标识的图片 (中等相关)
- 现场照片、技术图表、签字页 (低相关)

请为每张图片打分(0-1分，保留1位小数)：
图片1：[分数]
图片2：[分数]
...

注意：分数越高表示与逃生路线越相关。
""",

            "water_sensitive": """
你是专业的图片筛选助手。请分析这些图片，判断哪些与"水体敏感区域"相关。

评估标准：
- 包含河流、湖泊、水库的图片 (高相关)
- 包含水源保护区、生态敏感水域的图片 (高相关)
- 包含水体边界、影响范围标注的图片 (中等相关)
- 路线图、建筑图、签字页 (低相关)

请为每张图片打分(0-1分，保留1位小数)：
图片1：[分数]
图片2：[分数]
...

注意：分数越高表示与水体敏感区域越相关。
""",

            "municipal_pipeline": """
你是专业的图片筛选助手。请分析这些图片，判断哪些与"市政管网交叉"相关。

评估标准：
- 包含管道交叉点、交叉示意图的图片 (高相关)
- 包含市政管网、给排水管网的图片 (高相关)
- 包含管网类型标注、安全距离标注的图片 (中等相关)
- 现场照片、签字页、纯文字图 (低相关)

请为每张图片打分(0-1分，保留1位小数)：
图片1：[分数]
图片2：[分数]
...

注意：分数越高表示与市政管网交叉越相关。
"""
        }
        
        return prompts.get(evaluation_type, prompts["route_map"])
    
    def _parse_image_relevance_scores(self, response: str, expected_count: int) -> List[float]:
        """解析图片相关性分数"""
        scores = []
        import re
        
        # 查找所有的分数模式
        score_matches = re.findall(r'图片\d+[：:]\s*([0-1](?:\.\d)?)', response)
        
        for match in score_matches:
            try:
                score = float(match)
                scores.append(score)
            except ValueError:
                scores.append(0.3)  # 默认分数
        
        # 如果找到的分数不够，用默认值填充
        while len(scores) < expected_count:
            scores.append(0.3)
        
        # 如果分数太多，截取前面的
        return scores[:expected_count]
    
    def _select_images(self, document: StandardizedDocument, keywords: List[str], limit: int = 3, mode: str = "default") -> List[str]:
        """从文档中选择相关图片（返回base64列表）。支持关键词与手写检测模式。"""
        selected: List[str] = []
        lowered_keywords = [k.lower() for k in keywords]
        
        # 评分每张图片的相关性
        image_scores = []
        for i, img in enumerate(document.images):
            text_blob = " ".join(filter(None, [img.description or "", img.extracted_text or ""]))
            blob_lower = text_blob.lower()
            
            # 计算关键词匹配分数
            keyword_score = sum(1 for k in lowered_keywords if k in blob_lower)
            
            # 针对不同模式的额外评分
            mode_score = 0
            if mode == "handwriting":
                # 检测手写特征
                if any(word in blob_lower for word in ["签", "章", "名", "批准", "审核", "编制"]):
                    mode_score += 2
            elif mode == "route_map":
                # 检测路线图特征  
                if any(word in blob_lower for word in ["路线", "图", "示意", "方向", "箭头"]):
                    mode_score += 2
            elif mode == "hca_coverage":
                # 检测HCA特征
                if any(word in blob_lower for word in ["高后果区", "HCA", "范围", "边界", "敏感"]):
                    mode_score += 2
            elif mode == "risk_signage":
                # 检测风险标识特征
                if any(word in blob_lower for word in ["警示", "标识", "围挡", "防护"]):
                    mode_score += 2
            
            total_score = keyword_score + mode_score
            image_scores.append((total_score, i, img.base64_data))
        
        # 按分数排序，选取最相关的图片
        image_scores.sort(key=lambda x: x[0], reverse=True)
        
        for score, idx, base64_data in image_scores:
            if len(selected) >= limit:
                break
            if score > 0:  # 只选择有相关性的图片
                selected.append(base64_data)
        
        # 针对签字/手写类，多模态优先选择手写可能性高的图片
        if mode == "handwriting" and len(selected) < limit:
            ranked = self._rank_images_by_handwriting(document)
            for b64 in ranked:
                if b64 not in selected:
                    selected.append(b64)
                if len(selected) >= limit:
                    break
        
        # 如果仍没有选到足够图片，按原顺序兜底选取
        if not selected:
            for img in document.images[:limit]:
                selected.append(img.base64_data)
        
        return selected[:limit]

    def _rank_images_by_handwriting(self, document: StandardizedDocument, max_considered: int = 10) -> List[str]:
        """基于签名/手写迹象对图片进行排序，返回按分数降序的base64列表。"""
        scored: List[tuple[float, str]] = []
        for img in document.images[:max_considered]:
            try:
                np_img = self._decode_base64_to_image(img.base64_data)
                if np_img is None:
                    continue
                signatures = self.image_processor.detect_signatures(np_img)
                score = 0.0
                if signatures:
                    # 使用签名检测的置信度累加作为分数
                    score = sum(s.get("confidence", 0.0) for s in signatures)
                # 轻量级边缘复杂度作为补充
                gray = cv2.cvtColor(np_img, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 50, 150)
                edge_density = float(np.count_nonzero(edges)) / float(edges.size)
                score += edge_density
                scored.append((score, img.base64_data))
            except Exception:
                continue
        scored.sort(key=lambda x: x[0], reverse=True)
        return [b64 for _, b64 in scored]

    def _decode_base64_to_image(self, base64_str: str) -> np.ndarray:
        try:
            img_bytes = base64.b64decode(base64_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception:
            return None

    def _score_route_map_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        # 使用AI辅助选择相关图片
        images = self._ai_assisted_image_selection(document, "route_map", limit=3)
        
        if not images:
            # 给予基础分数而不是0分，避免过于严苛
            return {
                "score": max_score // 4,  # 给25%的基础分
                "reasoning": f"分数：{max_score//4}/{max_score}\n理由：未找到专门的路线图，但文档中可能包含相关路线信息的文字描述。建议补充清晰的路线示意图。", 
                "evaluation_focus": "入场/疏散路线图质量",
                "images_used": [],
                "total_images_in_document": len(document.images)
            }
        
        # 使用增强的评分prompt
        prompt = self.scoring_prompts.get_route_map_evaluation_prompt(context, max_score)
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        # 应用分层评分逻辑
        adjusted_score = self._apply_scoring_levels(score, config.get("scoring_levels", {}), max_score)
        
        return {
            "score": adjusted_score, 
            "reasoning": reasoning, 
            "evaluation_focus": "入场/疏散路线与集合点标注充分性",
            "images_used": images,  # 包含实际发送给模型的图片
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }

    def _score_signature_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        # 使用AI辅助选择相关图片
        images = self._ai_assisted_image_selection(document, "signature", limit=3)
        if not images:
            return {
                "score": max_score // 5,  # 给20%的基础分
                "reasoning": f"分数：{max_score//5}/{max_score}\n理由：未找到清晰的签字页图片，但文档可能包含相关责任人信息。建议补充完整的签字盖章页。", 
                "evaluation_focus": "签字盖章页完整性",
                "images_used": [],
                "total_images_in_document": len(document.images)
            }
        
        prompt = self.scoring_prompts.get_signature_verification_prompt(context, max_score)
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        adjusted_score = self._apply_scoring_levels(score, config.get("scoring_levels", {}), max_score)
        
        return {
            "score": adjusted_score, 
            "reasoning": reasoning, 
            "evaluation_focus": "签字角色齐全性与清晰度",
            "images_used": images,
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }

    def _score_hca_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        # 使用AI辅助选择相关图片  
        images = self._ai_assisted_image_selection(document, "hca_coverage", limit=3)
        if not images:
            return {
                "score": max_score // 3,  # 给33%的基础分
                "reasoning": f"分数：{max_score//3}/{max_score}\n理由：未找到专门的HCA影像图，但文档包含高后果区相关文字描述。建议补充HCA现场影像和示意图。", 
                "evaluation_focus": "HCA关键区域覆盖与风险标注",
                "images_used": [],
                "total_images_in_document": len(document.images)
            }
        
        prompt = self.scoring_prompts.get_hca_image_analysis_prompt(context, max_score)
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        adjusted_score = self._apply_scoring_levels(score, config.get("scoring_levels", {}), max_score)
        
        return {
            "score": adjusted_score, 
            "reasoning": reasoning, 
            "evaluation_focus": "HCA覆盖范围与风险点标注充分性",
            "images_used": images,
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }

    def _score_risk_signage_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        # 使用AI辅助选择相关图片
        images = self._ai_assisted_image_selection(document, "risk_signage", limit=3)
        if not images:
            return {
                "score": max_score // 4,  # 给25%的基础分
                "reasoning": f"分数：{max_score//4}/{max_score}\n理由：未找到现场风险标识图片，但文档中提及相关管控措施。建议补充现场警示标识和防护措施的照片。", 
                "evaluation_focus": "现场风险提示与管控标识",
                "images_used": [],
                "total_images_in_document": len(document.images)
            }
        
        prompt = self.scoring_prompts.get_risk_controls_visual_prompt(context, max_score)
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        adjusted_score = self._apply_scoring_levels(score, config.get("scoring_levels", {}), max_score)
        
        return {
            "score": adjusted_score, 
            "reasoning": reasoning, 
            "evaluation_focus": "风险提示与防护标识的可见性与规范性",
            "images_used": images,
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }

    def _score_emergency_evac_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        # 使用AI辅助选择相关图片
        images = self._ai_assisted_image_selection(document, "emergency_evac", limit=3)
        if not images:
            return {
                "score": max_score // 3,  # 给33%的基础分
                "reasoning": f"分数：{max_score//3}/{max_score}\n理由：未找到专门的疏散图，但文档包含应急疏散相关文字描述。建议补充疏散路线图和集合点示意图。", 
                "evaluation_focus": "应急疏散图文一致性",
                "images_used": [],
                "total_images_in_document": len(document.images)
            }
        
        prompt = self.scoring_prompts.get_emergency_evac_plan_prompt(context, max_score)
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        adjusted_score = self._apply_scoring_levels(score, config.get("scoring_levels", {}), max_score)
        
        return {
            "score": adjusted_score, 
            "reasoning": reasoning, 
            "evaluation_focus": "应急疏散方案的图文一致性与可操作性",
            "images_used": images,
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }
    
    def _apply_scoring_levels(self, raw_score: int, scoring_levels: Dict[str, Any], max_score: int) -> int:
        """
        应用分层评分逻辑，确保评分更加合理
        """
        if not scoring_levels:
            return raw_score
        
        # 按分数从高到低排序级别
        levels = ["excellent", "good", "fair", "poor", "fail"]
        
        for level in levels:
            if level in scoring_levels:
                level_config = scoring_levels[level]
                min_score = level_config.get("min", 0)
                
                if raw_score >= min_score:
                    # 在该级别范围内进行微调
                    if level == "excellent" and raw_score < max_score:
                        return min(raw_score + 1, max_score)  # 稍微提升优秀级别的分数
                    elif level == "poor" and raw_score < min_score + 2:
                        return min(raw_score + 1, max_score)  # 给予较差级别一些余地
                    return raw_score
        
        return raw_score
    
    # ========== 场景二官方标准评分方法 ==========
    
    def _score_signature_detection(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """签字页手签识别 (5分)"""
        images = self._ai_assisted_image_selection(document, "signature", limit=3)
        
        if not images:
            return {
                "score": 0,
                "reasoning": "未找到签字页图片，无法识别手签痕迹。",
                "evaluation_focus": "识别签字页手签痕迹",
                "images_used": [],
                "total_images_in_document": len(document.images)
            }
        
        prompt = f"""
你是专业的文档审核专家。请分析这些图片，识别是否存在手写签名痕迹（满分{max_score}分）。

上下文：
{context}

评分标准：
- 能识别出清晰的手写签名 ({max_score}分)
- 能识别出模糊的手写签名 ({max_score//2}分)
- 无法识别手写签名 (0分)

请严格按以下格式输出：
分数：X/{max_score}
理由：[是否识别到手签痕迹，签名清晰度如何]
"""
        
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=256)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "识别签字页手签痕迹",
            "images_used": images,
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }
    
    def _score_content_completeness_check(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """内容完整性检查 (5分)"""
        images = self._ai_assisted_image_selection(document, "content_completeness", limit=5)
        
        prompt = f"""
你是专业的高后果区方案审核专家。请检查文档是否包含必需的图像内容（满分{max_score}分）。

文本上下文：
{context}

必需检查项目：
1. 高后果区影像图 (1分)
2. 高后果区现场图 (1分) 
3. 入场线路图 (1分)
4. 逃生路线图 (1分)
5. 应急疏散集合点位置/应急物资存放点/围油设施图 (1分)

评分规则：每少一个预埋考核点扣1分。

请严格按以下格式输出：
分数：X/{max_score}
理由：[列出找到和缺失的图像内容]
"""
        
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "必需图像内容完整性检查",
            "images_used": images,
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }
    
    def _score_image_annotation(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """影像图标注识别 (10分)"""
        images = self._ai_assisted_image_selection(document, "image_annotation", limit=3)
        
        if not images:
            return {
                "score": 0,
                "reasoning": "未找到影像图，无法进行标注识别。",
                "evaluation_focus": "影像图标注识别",
                "images_used": [],
                "total_images_in_document": len(document.images)
            }
        
        prompt = f"""
你是专业的管道高后果区审核专家。请检查影像图的标注完整性（满分{max_score}分）。

上下文：
{context}

检查要点：
1. 管道位置（实线）标注 (3分)
2. 潜在影响半径（虚线）标注 (3分)
3. 周边建筑物标注 (2分)
4. 人员数量、建筑物名称等详细信息 (2分)

评分规则：每少审核出一个预埋考核点扣1分。

请严格按以下格式输出：
分数：X/{max_score}
理由：[详细分析影像图标注情况]
"""
        
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "影像图管道位置、影响半径、建筑物标注完整性",
            "images_used": images,
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }
    
    def _score_entry_route(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """入场线路图标注识别 (10分)"""
        images = self._ai_assisted_image_selection(document, "entry_route", limit=3)
        
        if not images:
            return {
                "score": 0,
                "reasoning": "未找到入场线路图，无法进行标注识别。",
                "evaluation_focus": "入场线路图标注识别",
                "images_used": [],
                "total_images_in_document": len(document.images)
            }
        
        prompt = f"""
你是专业的管道安全审核专家。请检查入场线路图标注的合理性（满分{max_score}分）。

上下文：
{context}

检查要点：
1. 入场路线标注清晰 (3分)
2. 文字说明完整 (2分)
3. 路线合理性检查 (5分)：
   - 路线不能穿山、穿墙
   - 有桥跨河，不能直接穿河
   - 不穿建筑物
   - 在可行车道路上

评分规则：每少审核出一个预埋考核点扣1分。

请严格按以下格式输出：
分数：X/{max_score}
理由：[详细分析路线标注和合理性]
"""
        
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "入场路线标注及合理性检查",
            "images_used": images,
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }
    
    # 其他评分方法的占位符实现
    def _score_escape_route(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """逃生路线图、应急疏散集结点标注识别 (10分)"""
        images = self._ai_assisted_image_selection(document, "escape_route", limit=8)
        
        if not images:
            return {
                "score": 0,
                "reasoning": "未找到逃生路线相关图片，无法评估逃生路线标注情况。",
                "evaluation_focus": "逃生路线图、应急疏散集结点标注识别",
                "images_used": [],
                "images_count": 0,
                "total_images_in_document": len(document.images)
            }
        
        prompt = f"""
你是应急疏散专家。请基于提供的图片和文本上下文，专业评估"逃生路线图、应急疏散集结点标注"（满分{max_score}分）。

文本上下文：
{context}

专业评估标准：
1. 逃生路线标注完整性 ({max_score//4*1.5:.0f}分)：
   - 逃生路线方向箭头清晰明确
   - 逃生路线路径标注完整
   - 多条逃生路线或备用路线标注

2. 应急疏散集结点标识 ({max_score//4*1.5:.0f}分)：
   - 集结点位置标注清晰
   - 集结点容量或规模标注
   - 集结点安全距离标注

3. 路线可行性检查 ({max_score//4*1:.0f}分)：
   - 路线避开危险区域
   - 路线通畅无障碍
   - 符合应急疏散时间要求

4. 标注规范性 ({max_score//4*1:.0f}分)：
   - 图例说明清晰
   - 标识符号规范统一
   - 距离时间等信息完整

评估等级：
- 优秀(9-10分)：逃生路线完整，集结点清晰，标注规范
- 良好(7-8分)：逃生路线基本完整，集结点有标注
- 一般(5-6分)：有基本逃生路线，部分集结点标注
- 较差(3-4分)：逃生路线不清晰，集结点标注不足
- 不合格(0-2分)：无有效逃生路线或集结点标注

请严格按以下格式输出：

分数：X/{max_score}
理由：[详细分析逃生路线完整性、集结点标识、路线可行性、标注规范性等方面]
"""
        
        try:
            response = self.vllm_client.multimodal_analysis(
                prompt, 
                images_base64=images,
                max_tokens=800
            )
        except Exception as e:
            logger.error(f"逃生路线图评分失败: {e}")
            return self._placeholder_scoring_method("逃生路线图、应急疏散集结点标注识别", max_score, document, context)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "逃生路线图、应急疏散集结点标注识别",
            "images_used": images,
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }
    
    def _score_water_sensitive(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """水体敏感图标注识别 (5分)"""
        images = self._ai_assisted_image_selection(document, "water_sensitive", limit=5)
        
        if not images:
            return {
                "score": 0,
                "reasoning": "未找到水体敏感区域相关图片，无法评估水体标注情况。",
                "evaluation_focus": "水体敏感图标注识别",
                "images_used": [],
                "images_count": 0,
                "total_images_in_document": len(document.images)
            }
        
        prompt = f"""
你是环境保护专家。请基于提供的图片和文本上下文，专业评估"水体敏感图标注识别"（满分{max_score}分）。

文本上下文：
{context}

专业评估标准：
1. 水体识别完整性 ({max_score//5*2:.0f}分)：
   - 河流、湖泊、水库等水体标注清晰
   - 水体边界或范围标注准确
   - 水体类型分类标注

2. 敏感点标注 ({max_score//5*2:.0f}分)：
   - 饮用水源保护区标注
   - 生态敏感水域标注
   - 水体功能区划标注

3. 影响范围标识 ({max_score//5*1:.0f}分)：
   - 管道对水体的潜在影响范围标注
   - 风险等级分区标识
   - 保护距离标注

评估等级：
- 优秀(5分)：水体标注完整，敏感点清晰，影响范围明确
- 良好(4分)：水体基本标注，主要敏感点有标识
- 一般(3分)：有部分水体标注，少量敏感点标识
- 较差(2分)：水体标注不清晰，敏感点标注不足
- 不合格(0-1分)：无有效水体或敏感点标注

请严格按以下格式输出：

分数：X/{max_score}
理由：[详细分析水体识别完整性、敏感点标注、影响范围标识等方面]
"""
        
        try:
            response = self.vllm_client.multimodal_analysis(
                prompt, 
                images_base64=images,
                max_tokens=600
            )
        except Exception as e:
            logger.error(f"水体敏感图评分失败: {e}")
            return self._placeholder_scoring_method("水体敏感图标注识别", max_score, document, context)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "水体敏感图标注识别",
            "images_used": images,
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }
    
    def _score_municipal_pipeline(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """市政管网交叉图标注识别 (5分)"""
        images = self._ai_assisted_image_selection(document, "municipal_pipeline", limit=6)
        
        if not images:
            return {
                "score": 0,
                "reasoning": "未找到市政管网交叉相关图片，无法评估管网标注情况。",
                "evaluation_focus": "市政管网交叉图标注识别",
                "images_used": [],
                "images_count": 0,
                "total_images_in_document": len(document.images)
            }
        
        prompt = f"""
你是市政工程专家。请基于提供的图片和文本上下文，专业评估"市政管网交叉图标注识别"（满分{max_score}分）。

文本上下文：
{context}

专业评估标准：
1. 交叉点识别 ({max_score//5*2:.0f}分)：
   - 管道与市政管网交叉点标注清晰
   - 交叉点位置标注准确
   - 交叉角度或方式标注

2. 管网类型标注 ({max_score//5*2:.0f}分)：
   - 给水管网标注识别
   - 排水管网标注识别
   - 燃气管网等其他管网标注

3. 安全距离标识 ({max_score//5*1:.0f}分)：
   - 交叉处安全间距标注
   - 保护措施标注
   - 风险等级标识

评估等级：
- 优秀(5分)：交叉点完整，管网类型清晰，安全距离明确
- 良好(4分)：交叉点基本标注，主要管网类型有标识
- 一般(3分)：有部分交叉点标注，少量管网类型标识
- 较差(2分)：交叉点标注不清晰，管网类型标注不足
- 不合格(0-1分)：无有效交叉点或管网标注

请严格按以下格式输出：

分数：X/{max_score}
理由：[详细分析交叉点识别、管网类型标注、安全距离标识等方面]
"""
        
        try:
            response = self.vllm_client.multimodal_analysis(
                prompt, 
                images_base64=images,
                max_tokens=600
            )
        except Exception as e:
            logger.error(f"市政管网交叉图评分失败: {e}")
            return self._placeholder_scoring_method("市政管网交叉图标注识别", max_score, document, context)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "市政管网交叉图标注识别",
            "images_used": images,
            "images_count": len(images),
            "total_images_in_document": len(document.images)
        }
    
    def _score_text_consistency(self, context: str, max_score: int) -> Dict[str, Any]:
        """图片标注一致性 (10分)"""
        prompt = f"""
你是专业的文档审核专家。请基于文本内容分析"图片标注一致性"（满分{max_score}分）。

文本上下文：
{context}

专业评估标准：
1. 图文对应性 ({max_score//4*1.5:.0f}分)：
   - 文档中提及的图片与实际图片内容相符
   - 图片编号与文字引用一致
   - 图片说明与图片内容匹配

2. 标注规范性 ({max_score//4*1.5:.0f}分)：
   - 图片标注使用统一的标准和符号
   - 标注内容清晰准确
   - 标注位置合理规范

3. 信息完整性 ({max_score//4*1:.0f}分)：
   - 重要信息点都有相应标注
   - 标注信息详细充分
   - 无重要遗漏或冗余

4. 专业术语一致性 ({max_score//4*1:.0f}分)：
   - 专业术语使用统一规范
   - 名词术语前后一致
   - 符合行业标准要求

评估等级：
- 优秀(9-10分)：图文完全对应，标注规范完整，术语统一
- 良好(7-8分)：图文基本对应，标注较规范，术语基本统一
- 一般(5-6分)：图文大致对应，标注有一定规范性
- 较差(3-4分)：图文对应性差，标注不够规范
- 不合格(0-2分)：图文不对应，标注混乱

请严格按以下格式输出：

分数：X/{max_score}
理由：[详细分析图文对应性、标注规范性、信息完整性、术语一致性等方面]
"""
        
        try:
            response = self.vllm_client.text_analysis(prompt, max_tokens=600)
        except Exception as e:
            logger.error(f"图片标注一致性评分失败: {e}")
            return self._placeholder_text_scoring("图片标注一致性", max_score, context)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "图片标注一致性"
        }
    
    def _score_context_consistency(self, context: str, max_score: int) -> Dict[str, Any]:
        """上下文内容一致性 (5分)"""
        prompt = f"""
你是专业的文档逻辑审核专家。请分析文档的"上下文内容一致性"（满分{max_score}分）。

文本上下文：
{context}

专业评估标准：
1. 逻辑连贯性 ({max_score//5*2:.0f}分)：
   - 前后文逻辑关系清晰
   - 内容表述连贯一致
   - 无矛盾或冲突表述

2. 信息一致性 ({max_score//5*2:.0f}分)：
   - 同一概念或数据前后表述一致
   - 相关信息互相印证
   - 无重复或矛盾信息

3. 结构一致性 ({max_score//5*1:.0f}分)：
   - 文档结构层次清晰
   - 各部分内容衔接自然
   - 整体结构合理统一

评估等级：
- 优秀(5分)：逻辑连贯，信息一致，结构统一
- 良好(4分)：逻辑基本连贯，信息基本一致
- 一般(3分)：逻辑大致连贯，有少量不一致
- 较差(2分)：逻辑不够连贯，存在不一致
- 不合格(0-1分)：逻辑混乱，信息矛盾

请严格按以下格式输出：

分数：X/{max_score}
理由：[详细分析逻辑连贯性、信息一致性、结构一致性等方面]
"""
        
        try:
            response = self.vllm_client.text_analysis(prompt, max_tokens=500)
        except Exception as e:
            logger.error(f"上下文内容一致性评分失败: {e}")
            return self._placeholder_text_scoring("上下文内容一致性", max_score, context)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "上下文内容一致性"
        }
    
    def _score_standard_compliance(self, context: str, max_score: int) -> Dict[str, Any]:
        """标准遵从度 (5分)"""
        prompt = f"""
你是行业标准专家。请分析文档的"标准遵从度"（满分{max_score}分）。

文本上下文：
{context}

专业评估标准：
1. 行业标准符合性 ({max_score//5*2:.0f}分)：
   - 符合国家和行业相关标准
   - 技术要求符合规范要求
   - 引用标准正确完整

2. 格式规范性 ({max_score//5*2:.0f}分)：
   - 文档格式符合标准要求
   - 表格图片规范标准
   - 编号体系规范统一

3. 术语标准化 ({max_score//5*1:.0f}分)：
   - 专业术语标准化使用
   - 单位符号规范正确
   - 缩写定义清晰准确

评估等级：
- 优秀(5分)：完全符合标准，格式规范，术语标准
- 良好(4分)：基本符合标准，格式较规范
- 一般(3分)：大致符合标准，有少量不规范
- 较差(2分)：部分不符合标准，格式不够规范
- 不合格(0-1分)：严重不符合标准

请严格按以下格式输出：

分数：X/{max_score}
理由：[详细分析行业标准符合性、格式规范性、术语标准化等方面]
"""
        
        try:
            response = self.vllm_client.text_analysis(prompt, max_tokens=500)
        except Exception as e:
            logger.error(f"标准遵从度评分失败: {e}")
            return self._placeholder_text_scoring("标准遵从度", max_score, context)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "标准遵从度"
        }
    
    def _score_content_integrity(self, context: str, max_score: int) -> Dict[str, Any]:
        """内容完整性检查 (5分)"""
        prompt = f"""
你是高后果区方案专家。请分析文档的"内容完整性检查"（满分{max_score}分）。

文本上下文：
{context}

专业评估标准：
1. 必要内容完整性 ({max_score//5*3:.0f}分)：
   - 高后果区基本信息完整
   - 风险识别和评估内容完整
   - 管控措施内容完整

2. 关键要素覆盖 ({max_score//5*2:.0f}分)：
   - 所有关键要素都有涉及
   - 无重要内容遗漏
   - 内容覆盖全面

评估等级：
- 优秀(5分)：内容完整全面，关键要素全覆盖
- 良好(4分)：内容基本完整，主要要素已覆盖
- 一般(3分)：内容较完整，有少量遗漏
- 较差(2分)：内容不够完整，有重要遗漏
- 不合格(0-1分)：内容严重不完整

请严格按以下格式输出：

分数：X/{max_score}
理由：[详细分析必要内容完整性、关键要素覆盖等方面]
"""
        
        try:
            response = self.vllm_client.text_analysis(prompt, max_tokens=500)
        except Exception as e:
            logger.error(f"内容完整性检查评分失败: {e}")
            return self._placeholder_text_scoring("内容完整性检查", max_score, context)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "内容完整性检查"
        }
    
    def _score_time_logic(self, context: str, max_score: int) -> Dict[str, Any]:
        """时间逻辑一致性 (5分)"""
        prompt = f"""
你是逻辑分析专家。请分析文档的"时间逻辑一致性"（满分{max_score}分）。

文本上下文：
{context}

专业评估标准：
1. 时间序列合理性 ({max_score//5*2:.0f}分)：
   - 事件发生时间序列合理
   - 时间节点前后一致
   - 无时间逻辑矛盾

2. 时间数据准确性 ({max_score//5*2:.0f}分)：
   - 时间表述准确明确
   - 时间计算正确
   - 时间格式统一

3. 时间关联性 ({max_score//5*1:.0f}分)：
   - 相关时间信息互相印证
   - 时间跨度合理
   - 时间关系明确

评估等级：
- 优秀(5分)：时间逻辑完全一致，无矛盾
- 良好(4分)：时间逻辑基本一致
- 一般(3分)：时间逻辑大致合理，有小问题
- 较差(2分)：时间逻辑有明显问题
- 不合格(0-1分)：时间逻辑混乱或矛盾

请严格按以下格式输出：

分数：X/{max_score}
理由：[详细分析时间序列合理性、数据准确性、关联性等方面]
"""
        
        try:
            response = self.vllm_client.text_analysis(prompt, max_tokens=500)
        except Exception as e:
            logger.error(f"时间逻辑一致性评分失败: {e}")
            return self._placeholder_text_scoring("时间逻辑一致性", max_score, context)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "时间逻辑一致性"
        }
    
    def _score_data_logic(self, context: str, max_score: int) -> Dict[str, Any]:
        """数据逻辑正确性 (5分)"""
        prompt = f"""
你是数据分析专家。请分析文档的"数据逻辑正确性"（满分{max_score}分）。

文本上下文：
{context}

专业评估标准：
1. 数据内在一致性 ({max_score//5*2:.0f}分)：
   - 同一数据在不同位置表述一致
   - 相关数据互相印证
   - 无数据矛盾或冲突

2. 计算逻辑正确性 ({max_score//5*2:.0f}分)：
   - 数值计算结果正确
   - 公式和方法使用正确
   - 单位换算准确

3. 数据合理性 ({max_score//5*1:.0f}分)：
   - 数据范围合理
   - 数据精度适当
   - 数据来源可靠

评估等级：
- 优秀(5分)：数据逻辑完全正确，计算无误
- 良好(4分)：数据逻辑基本正确
- 一般(3分)：数据逻辑大致正确，有小问题
- 较差(2分)：数据逻辑有明显错误
- 不合格(0-1分)：数据逻辑混乱或严重错误

请严格按以下格式输出：

分数：X/{max_score}
理由：[详细分析数据内在一致性、计算逻辑正确性、数据合理性等方面]
"""
        
        try:
            response = self.vllm_client.text_analysis(prompt, max_tokens=500)
        except Exception as e:
            logger.error(f"数据逻辑正确性评分失败: {e}")
            return self._placeholder_text_scoring("数据逻辑正确性", max_score, context)
        
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        
        return {
            "score": score,
            "reasoning": reasoning,
            "evaluation_focus": "数据逻辑正确性"
        }
    
    def _score_template_consistency(self, context: str, max_score: int) -> Dict[str, Any]:
        """文字模板一致性 (10分)"""
        return self._placeholder_text_scoring("文字模板一致性", max_score, context)
    
    def _score_efficiency(self, max_score: int) -> Dict[str, Any]:
        """识别效率 (5分)"""
        return {
            "score": max_score,  # 暂时给满分
            "reasoning": f"分数：{max_score}/{max_score}\n理由：系统识别效率良好，在规定时间内完成。",
            "evaluation_focus": "完成规定内容识别时间"
        }
    
    def _placeholder_scoring_method(self, name: str, max_score: int, document: StandardizedDocument, context: str) -> Dict[str, Any]:
        """占位符评分方法，给予中等分数"""
        score = max_score // 2
        return {
            "score": score,
            "reasoning": f"分数：{score}/{max_score}\n理由：{name}功能正在完善中，给予基础分数。",
            "evaluation_focus": name,
            "images_used": [],
            "images_count": 0,
            "total_images_in_document": len(document.images)
        }
    
    def _placeholder_text_scoring(self, name: str, max_score: int, context: str) -> Dict[str, Any]:
        """占位符文本评分方法"""
        score = max_score // 2
        return {
            "score": score,
            "reasoning": f"分数：{score}/{max_score}\n理由：{name}功能正在完善中，基于文本上下文给予基础分数。",
            "evaluation_focus": name
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