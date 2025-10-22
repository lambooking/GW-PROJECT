"""
文档分类器 - 自动识别场景一(作业指导书)或场景二(高后果区风险管控方案)
"""

import re
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DocumentClassifier:
    """文档分类器，用于识别文档属于哪个场景"""
    
    def __init__(self):
        # 场景一关键词 - 作业指导书
        self.scenario_one_keywords = [
            "作业指导书",
            "操作规程", 
            "岗位职责",
            "巡检",
            "操作规范",
            "应急预案",
            "培训",
            "安全作业",
            "管道保护",
            "防汛抗洪"
        ]
        
        # 场景二关键词 - 高后果区风险管控方案
        self.scenario_two_keywords = [
            "高后果区",
            "风险管控方案",
            "HCA",
            "风险评价",
            "人员密集型",
            "环境敏感型",
            "潜在影响半径",
            "应急疏散",
            "风险识别",
            "管控措施"
        ]
        
        # 场景一文档结构特征
        self.scenario_one_structure = [
            r"第?\s*[一二三四五六七八九十\d]+\s*章",  # 章节编号
            r"\d+\.\d+\.\d+",  # 多级编号
            r"附录\s*[A-Z]",  # 附录
            r"作业流程",
            r"操作步骤"
        ]
        
        # 场景二文档结构特征  
        self.scenario_two_structure = [
            r"基本信息表",
            r"风险评价.*结果",
            r"管控措施",
            r"应急预案",
            r"签字页",
            r"影像图",
            r"现场图"
        ]
    
    def classify_document(self, parsed_content: Dict[str, Any], file_name: Optional[str] = None) -> Dict[str, Any]:
        """
        分类文档
        
        Args:
            parsed_content: 解析后的文档内容
            file_name: 可选，原始文件名，用于增强型启发式判断
            
        Returns:
            分类结果字典
        """
        try:
            # 合并所有文本内容
            full_text = self._extract_full_text(parsed_content)
            head_text = full_text[:1000] if full_text else ""
            file_name_lower = (file_name or "").lower()
            
            # 计算关键词匹配分数
            scenario_one_score = self._calculate_keyword_score(full_text, self.scenario_one_keywords)
            scenario_two_score = self._calculate_keyword_score(full_text, self.scenario_two_keywords)
            
            # 计算结构特征分数
            scenario_one_structure_score = self._calculate_structure_score(full_text, self.scenario_one_structure)
            scenario_two_structure_score = self._calculate_structure_score(full_text, self.scenario_two_structure)
            
            # 文件名与首页强启发式加权（错误分场景常见于标题与文件名）
            # 文件名强信号
            if any(k in file_name_lower for k in ["作业指导书", "指导书"]):
                scenario_one_score += 3.0
            if any(k in file_name_lower for k in ["高后果区", "风险管控方案", "hca"]):
                scenario_two_score += 3.0

            # 首页/标题强信号
            if any(k in head_text for k in ["作业指导书", "操作规程", "岗位职责"]):
                scenario_one_score += 2.0
            if any(k in head_text for k in ["高后果区", "风险管控方案", "HCA"]):
                scenario_two_score += 2.0

            # 综合评分
            total_one_score = scenario_one_score + scenario_one_structure_score
            total_two_score = scenario_two_score + scenario_two_structure_score
            
            # 确定场景
            # 若分差很接近且标题/文件名指向性强，则优先按指向性决策
            margin = abs(total_one_score - total_two_score)
            if margin < 1.0:
                if any(k in file_name_lower for k in ["作业指导书", "指导书"]) or any(k in head_text for k in ["作业指导书", "操作规程", "岗位职责"]):
                    prefer_one = True
                elif any(k in file_name_lower for k in ["高后果区", "风险管控方案", "hca"]) or any(k in head_text for k in ["高后果区", "风险管控方案", "HCA"]):
                    prefer_one = False
                else:
                    prefer_one = total_one_score >= total_two_score
                if prefer_one:
                    scenario = "scenario_one"
                    scenario_name = "作业指导书"
                    confidence = max(0.5, total_one_score / (total_one_score + total_two_score) if (total_one_score + total_two_score) > 0 else 0.5)
                else:
                    scenario = "scenario_two"
                    scenario_name = "高后果区风险管控方案"
                    confidence = max(0.5, total_two_score / (total_one_score + total_two_score) if (total_one_score + total_two_score) > 0 else 0.5)
            elif total_one_score > total_two_score:
                scenario = "scenario_one"
                scenario_name = "作业指导书"
                confidence = total_one_score / (total_one_score + total_two_score)
            else:
                scenario = "scenario_two" 
                scenario_name = "高后果区风险管控方案"
                confidence = total_two_score / (total_one_score + total_two_score)
            
            return {
                "scenario": scenario,
                "scenario_name": scenario_name,
                "confidence": confidence,
                "scores": {
                    "scenario_one": {
                        "keyword_score": scenario_one_score,
                        "structure_score": scenario_one_structure_score,
                        "total_score": total_one_score
                    },
                    "scenario_two": {
                        "keyword_score": scenario_two_score,
                        "structure_score": scenario_two_structure_score,
                        "total_score": total_two_score
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"文档分类失败: {e}")
            return {
                "scenario": "unknown",
                "scenario_name": "未知",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _extract_full_text(self, parsed_content: Dict[str, Any]) -> str:
        """提取文档的全部文本内容"""
        full_text = ""
        
        # 提取文本内容
        if "text_content" in parsed_content:
            for text_item in parsed_content["text_content"]:
                full_text += text_item.get("content", "") + " "
        
        # 提取表格内容
        if "tables" in parsed_content:
            for table in parsed_content["tables"]:
                if "data" in table:
                    for row in table["data"]:
                        full_text += " ".join(row) + " "
        
        return full_text
    
    def _calculate_keyword_score(self, text: str, keywords: list) -> float:
        """计算关键词匹配分数"""
        score = 0.0
        text_lower = text.lower()
        
        for keyword in keywords:
            count = text_lower.count(keyword.lower())
            if count > 0:
                # 使用对数函数避免单个关键词过度影响
                score += min(count * 0.5, 2.0)
        
        return score
    
    def _calculate_structure_score(self, text: str, patterns: list) -> float:
        """计算文档结构特征分数"""
        score = 0.0
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                score += min(len(matches) * 0.3, 1.0)
        
        return score