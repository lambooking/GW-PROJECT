"""
基于RAG知识库的智能评分引擎
动态检索相关内容，为每个评分项生成针对性的上下文
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import re
import base64
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time

from .rag_knowledge_base import RAGKnowledgeBase
from .vllm_client import VLLMInferenceClient
from .prompts import ScoringPrompts
from .signature_extractor import SignatureExtractor
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
        # 封面签字抽取器（仅用于场景二签字评分）
        self.signature_extractor = SignatureExtractor()

        
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
        
        # 场景二评分项配置（多模态为主）
        self.scoring_criteria_scene2 = {
            "route_map_quality": {
                "name": "路线图完整性与清晰度",
                "weight": 0.2,
                "max_score": 20,
                "search_queries": [
                    "入场线路", "疏散路线", "逃生路线", "集合点"
                ],
                "context_length": 1200,
                "image_keywords": ["线路", "路线", "疏散", "逃生", "集合点", "路线图"],
                "type": "multimodal_route"
            },
            "hca_coverage": {
                "name": "HCA影像覆盖与风险标注",
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
                    "签字", "签章", "批准", "审核", "编制", "评审意见", "签发意见", "日期"
                ],
                "context_length": 800,
                "pages": [1, 2, 3],
                "image_keywords": [
                    "签字", "签章", "签名", "盖章", "签字页",
                    "编制", "审核", "批准", "评审意见", "签发意见",
                    "年", "月", "日", "校对", "评审组长", "单位"
                ],
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
    def _select_images(self, document: StandardizedDocument, keywords: List[str], limit: int = 3) -> List[str]:
        """基于关键词与OCR结果优选相关图片；若未命中则回退为前N张。
        对签字/签章类评分项增加CV启发式优先级（红章/表格线密集度）。
        """
        selected: List[str] = []
        normalized_keywords = [k.lower() for k in (keywords or [])]
        is_signature_task = any(k in ("签字签章签名盖章签字页") for k in normalized_keywords)

        # 1) 先按OCR文本匹配关键词（并按命中+CV分数排序）
        if normalized_keywords:
            scored_images = []
            for img in document.images:
                if not img.base64_data:
                    continue
                ocr_text = (img.extracted_text or "").lower()
                hit = sum(1 for k in normalized_keywords if k in ocr_text)
                cv_bonus = self._estimate_signature_relevance(img.base64_data) if is_signature_task else 0.0
                scored_images.append((hit + cv_bonus, img.base64_data))

            scored_images.sort(key=lambda x: x[0], reverse=True)
            for score, b64 in scored_images:
                if score <= 0:
                    continue
                selected.append(b64)
                if len(selected) >= limit:
                    break

        # 2) 若未选满，则回退补齐到limit
        if len(selected) < limit:
            if is_signature_task:
                scored_fallback = []
                for img in document.images:
                    if not img.base64_data or img.base64_data in selected:
                        continue
                    score = self._estimate_signature_relevance(img.base64_data)
                    scored_fallback.append((score, img.base64_data))
                scored_fallback.sort(key=lambda x: x[0], reverse=True)
                for score, b64 in scored_fallback:
                    selected.append(b64)
                    if len(selected) >= limit:
                        break
            else:
                for img in document.images:
                    if not img.base64_data or img.base64_data in selected:
                        continue
                    selected.append(img.base64_data)
                    if len(selected) >= limit:
                        break

        logger.info(
            f"多模态评分将发送 {len(selected)} 张图片至模型（limit={limit}，文档共有 {len(document.images)} 张，关键词={keywords}）。首图base64长度={len(selected[0]) if selected else 0}"
        )
        return selected

    def _estimate_signature_relevance(self, image_base64: str) -> float:
        """估计图片与签字/签章页的相关性分数（0~1）。
        简单启发式：红色像素占比（盖章）+ 横竖线密度（表单版式）。
        """
        try:
            if image_base64.startswith("data:image"):
                b64 = image_base64.split(",", 1)[-1]
            else:
                b64 = image_base64
            img_bytes = base64.b64decode(b64)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                return 0.0

            h, w = img.shape[:2]
            if h == 0 or w == 0:
                return 0.0

            # 红色占比
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower_red1 = np.array([0, 80, 80])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 80, 80])
            upper_red2 = np.array([180, 255, 255])
            mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
            red_ratio = (np.count_nonzero(mask1) + np.count_nonzero(mask2)) / float(h * w)

            # 线密度
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 80, 180)
            lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=min(w, h) * 0.2, maxLineGap=10)
            line_count = 0 if lines is None else len(lines)
            line_density = min(1.0, line_count / 20.0)

            # 白底占比（签批表通常为白纸黑字）
            white_mask = cv2.inRange(gray, 230, 255)
            white_ratio = np.count_nonzero(white_mask) / float(h * w)

            # 版式方向（竖版更常见）
            portrait_boost = 0.15 if (h / max(1, w)) > 1.1 else 0.0

            score = red_ratio * 6.0 + line_density * 0.6 + white_ratio * 0.4 + portrait_boost
            score = float(min(1.0, score))
            return float(score)
        except Exception:
            return 0.0



    def _score_route_map_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        images = self._select_images(document, config.get("image_keywords", []), limit=3)
        if not images:
            return {"score": 0, "reasoning": "未找到与路线相关的图片", "evaluation_focus": "入场/疏散路线图质量", "images_used": [], "images_count": 0, "total_images_in_document": len(document.images)}
        prompt = self.scoring_prompts.get_route_map_evaluation_prompt(context, max_score)
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        return {"score": score, "reasoning": reasoning, "evaluation_focus": "入场/疏散路线与集合点标注充分性", "images_used": images, "images_count": len(images), "total_images_in_document": len(document.images)}

    def _score_signature_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """签字盖章评分：仅在封面/前两页（扩展到第3页）进行检测与一致性校验。

        评分构成（总分 max_score）：
        - 覆盖度 50%：编制/审核/批准三角色覆盖情况
        - 时序   30%：编制≤审核≤批准（若有日期）
        - 一致性 20%：姓名/日期与文本/表格元数据一致
        """

        # 1) 仅封面前3页抽取签字信息
        pages_conf = config.get("pages", [1, 2, 3])
        sig_records = self.signature_extractor.extract_signatures_from_cover_pages(document, max_pages=max(pages_conf) if pages_conf else 3)

        if not sig_records:
            return {
                "score": 0,
                "reasoning": "前3页未检测到有效签字/盖章候选",
                "evaluation_focus": "签字页存在性与要素完整",
                "signature_summary": {"coverage": 0, "roles": {}, "date_order_ok": None, "consistency_ok": None},
                "images_count": len(document.images),
                "total_images_in_document": len(document.images)
            }

        # 2) 结构化角色->最新记录（按置信度挑高者）
        role_to_best: Dict[str, Tuple[float, Any]] = {}
        for r in sig_records:
            key = (r.role or "")
            if not key:
                continue
            if key not in role_to_best or r.confidence > role_to_best[key][0]:
                role_to_best[key] = (r.confidence, r)

        have_roles = set(role_to_best.keys())
        needed = {"编制", "审核", "批准"}
        covered = needed & have_roles
        coverage_ratio = len(covered) / len(needed)

        # 3) 日期时序
        def parse_date(d: Optional[str]) -> Optional[datetime]:
            if not d:
                return None
            try:
                d = d.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-")
                parts = [p for p in d.split("-") if p]
                if len(parts) >= 3:
                    y, m, dd = int(parts[0]), int(parts[1]), int(parts[2])
                    return datetime(y, m, dd)
                return None
            except Exception:
                return None

        dates = {role: parse_date(getattr(role_to_best[role][1], "date", None)) for role in covered}
        date_order_ok = None
        if all(role in dates and dates[role] is not None for role in ["编制", "审核", "批准"] if role in covered):
            seq = [dates.get("编制"), dates.get("审核"), dates.get("批准")]
            seq = [d for d in seq if d is not None]
            date_order_ok = all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1))

        # 4) 与文本/表格元数据一致性（姓名/日期）——简化：在上下文中查找姓名/日期字符串
        context_text = context[:2000]
        consistency_hits = 0
        consistency_checks = 0
        for role in covered:
            rec = role_to_best[role][1]
            if rec.name:
                consistency_checks += 1
                if rec.name in context_text:
                    consistency_hits += 1
            if rec.date:
                consistency_checks += 1
                if rec.date.replace(" ", "") in context_text.replace(" ", ""):
                    consistency_hits += 1
        consistency_ok = (consistency_hits / consistency_checks) >= 0.6 if consistency_checks > 0 else None

        # 5) 计分
        coverage_score = coverage_ratio * (max_score * 0.5)
        order_score = (max_score * 0.3) if (date_order_ok is True) else 0
        consistency_score = (max_score * 0.2) if (consistency_ok is True) else 0
        score = int(round(coverage_score + order_score + consistency_score))

        reasoning_parts = [
            f"角色覆盖：{len(covered)}/3（{sorted(list(covered))}）",
            f"日期时序：{'正常' if date_order_ok else ('无法判定' if date_order_ok is None else '异常')}",
            f"文本一致性：{'通过' if consistency_ok else ('无法判定' if consistency_ok is None else '未通过')}"
        ]

        return {
            "score": min(score, max_score),
            "reasoning": "；".join(reasoning_parts),
            "evaluation_focus": "封面/前两页签字要素覆盖、日期时序与一致性",
            "signature_summary": {
                "coverage": coverage_ratio,
                "roles": {r: {
                    "name": getattr(role_to_best[r][1], "name", None),
                    "date": getattr(role_to_best[r][1], "date", None),
                    "confidence": role_to_best[r][0]
                } for r in covered},
                "date_order_ok": date_order_ok,
                "consistency_ok": consistency_ok
            },
        }

    def _score_hca_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        images = self._select_images(document, config.get("image_keywords", []), limit=3)
        if not images:
            return {"score": 0, "reasoning": "未找到HCA影像/示意图", "evaluation_focus": "HCA关键区域覆盖与风险标注", "images_used": [], "images_count": 0, "total_images_in_document": len(document.images)}
        prompt = self.scoring_prompts.get_hca_image_analysis_prompt(context, max_score)
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        return {"score": score, "reasoning": reasoning, "evaluation_focus": "HCA覆盖范围与风险点标注充分性", "images_used": images, "images_count": len(images), "total_images_in_document": len(document.images)}

    def _score_risk_signage_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        images = self._select_images(document, config.get("image_keywords", []), limit=3)
        if not images:
            return {"score": 0, "reasoning": "未找到风险提示/标识相关图片", "evaluation_focus": "现场风险提示与管控标识", "images_used": [], "images_count": 0, "total_images_in_document": len(document.images)}
        prompt = self.scoring_prompts.get_risk_controls_visual_prompt(context, max_score)
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        return {"score": score, "reasoning": reasoning, "evaluation_focus": "风险提示与防护标识的可见性与规范性", "images_used": images, "images_count": len(images), "total_images_in_document": len(document.images)}

    def _score_emergency_evac_multimodal(self, document: StandardizedDocument, context: str, max_score: int, config: Dict[str, Any]) -> Dict[str, Any]:
        images = self._select_images(document, config.get("image_keywords", []), limit=3)
        if not images:
            return {"score": 0, "reasoning": "未找到应急疏散/集合点相关图片", "evaluation_focus": "应急疏散图文一致性", "images_used": [], "images_count": 0, "total_images_in_document": len(document.images)}
        prompt = self.scoring_prompts.get_emergency_evac_plan_prompt(context, max_score)
        response = self.vllm_client.multimodal_analysis(prompt, images_base64=images, max_tokens=512)
        score, reasoning = self.scoring_prompts.parse_simple_response(response, max_score)
        return {"score": score, "reasoning": reasoning, "evaluation_focus": "应急疏散方案的图文一致性与可操作性", "images_used": images, "images_count": len(images), "total_images_in_document": len(document.images)}
    
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