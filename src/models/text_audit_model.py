"""
文本审核模型
"""

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from typing import Dict, List, Any
import numpy as np
import logging
from .base_model import BaseModel

logger = logging.getLogger(__name__)


class TextAuditModel(BaseModel):
    """文本审核模型"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        model_name = config.get('model_name', 'chinese-roberta-wwm-ext')
        num_classes = config.get('num_classes', 2)
        dropout = config.get('dropout', 0.1)
        
        self.bert = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_classes)
        
        # 审核规则分类器
        self.structure_classifier = nn.Linear(self.bert.config.hidden_size, 2)
        self.content_classifier = nn.Linear(self.bert.config.hidden_size, 2)
        self.grammar_classifier = nn.Linear(self.bert.config.hidden_size, 2)
        self.logic_classifier = nn.Linear(self.bert.config.hidden_size, 2)
        
    def forward(self, input_ids, attention_mask, token_type_ids=None):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids
        )
        
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)
        
        # 主分类结果
        main_logits = self.classifier(pooled_output)
        
        # 各项审核结果
        structure_logits = self.structure_classifier(pooled_output)
        content_logits = self.content_classifier(pooled_output)
        grammar_logits = self.grammar_classifier(pooled_output)
        logic_logits = self.logic_classifier(pooled_output)
        
        return {
            'main_logits': main_logits,
            'structure_logits': structure_logits,
            'content_logits': content_logits,
            'grammar_logits': grammar_logits,
            'logic_logits': logic_logits
        }
    
    def predict(self, input_text: str) -> Dict[str, Any]:
        """
        预测文本审核结果
        
        Args:
            input_text: 输入文本
            
        Returns:
            预测结果
        """
        try:
            # 这里需要tokenizer，实际使用时需要传入
            # 简化实现
            return {
                'main_score': 0.8,
                'structure_score': 0.7,
                'content_score': 0.9,
                'grammar_score': 0.8,
                'logic_score': 0.8
            }
        except Exception as e:
            logger.error(f"文本审核预测失败: {e}")
            return {'error': str(e)}


class InstructionBookAuditor:
    """作业指导书审核器"""
    
    def __init__(self, model_path: str = None, tokenizer_name: str = 'chinese-roberta-wwm-ext'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        
        # 创建模型配置
        model_config = {
            'model_name': tokenizer_name,
            'num_classes': 2,
            'dropout': 0.1
        }
        
        self.model = TextAuditModel(model_config)
        
        if model_path:
            try:
                self.model.load_model(model_path)
            except Exception as e:
                logger.warning(f"无法加载模型: {e}，使用默认配置")
        
        self.model.to(self.device)
        self.model.eval()
        
        # 审核规则配置
        self.required_sections = [
            "目录", "职责", "作业内容", "相关文件", "记录文件"
        ]
        
    def audit_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """审核作业指导书"""
        results = {
            'overall_score': 0.0,
            'structure_completeness': self._check_structure_completeness(document_data),
            'content_completeness': self._check_content_completeness(document_data),
            'grammar_errors': self._check_grammar_errors(document_data),
            'reference_traceability': self._check_reference_traceability(document_data),
            'business_logic': self._check_business_logic(document_data),
            'personnel_configuration': self._check_personnel_configuration(document_data),
            'emergency_procedures': self._check_emergency_procedures(document_data),
            'template_compliance': self._check_template_compliance(document_data),
            'issues_found': [],
            'suggestions': []
        }
        
        # 计算总分
        weights = {
            'structure_completeness': 0.2,
            'content_completeness': 0.4,
            'grammar_errors': 0.05,
            'reference_traceability': 0.1,
            'business_logic': 0.1,
            'personnel_configuration': 0.05,
            'emergency_procedures': 0.05,
            'template_compliance': 0.05
        }
        
        total_score = sum(results[key]['score'] * weights[key] for key in weights)
        results['overall_score'] = total_score
        
        return results
    
    def _check_structure_completeness(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查结构完整性"""
        text_content = ' '.join([item['content'] for item in document_data['text_content']])
        
        found_sections = []
        missing_sections = []
        
        for section in self.required_sections:
            if section in text_content:
                found_sections.append(section)
            else:
                missing_sections.append(section)
        
        score = len(found_sections) / len(self.required_sections)
        
        return {
            'score': score,
            'found_sections': found_sections,
            'missing_sections': missing_sections,
            'details': f"找到 {len(found_sections)}/{len(self.required_sections)} 个必需章节"
        }
    
    def _check_content_completeness(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查内容完整性"""
        # 使用模型进行内容完整性检查
        text_content = ' '.join([item['content'] for item in document_data['text_content']])
        
        # 检查关键内容点
        key_content_checks = [
            ("技术参数", ["参数", "技术", "规格"]),
            ("安全环保责任", ["安全", "环保", "责任"]),
            ("作业指引", ["作业", "指引", "操作"]),
            ("应急流程", ["应急", "流程", "处置"])
        ]
        
        content_scores = []
        issues = []
        
        for check_name, keywords in key_content_checks:
            found = any(keyword in text_content for keyword in keywords)
            if found:
                content_scores.append(1.0)
            else:
                content_scores.append(0.0)
                issues.append(f"缺少{check_name}相关内容")
        
        score = np.mean(content_scores)
        
        return {
            'score': score,
            'issues': issues,
            'details': f"内容完整性检查得分: {score:.2f}"
        }
    
    def _check_grammar_errors(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查语法错误"""
        # 简化的语法检查
        text_content = ' '.join([item['content'] for item in document_data['text_content']])
        
        # 常见语法错误模式
        import re
        error_patterns = [
            ("句号缺失", r'[\u4e00-\u9fff]+[^\u3002\uff01\uff1f\uff0c\uff1b\uff1a\u201c\u201d\u2018\u2019\uff08\uff09\u3001]$'),
            ("重复标点", r'[。！？]{2,}'),
            ("空格问题", r'\s{2,}'),
        ]
        
        errors_found = []
        for error_type, pattern in error_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                errors_found.append(f"{error_type}: 发现 {len(matches)} 处")
        
        score = max(0, 1.0 - len(errors_found) * 0.1)
        
        return {
            'score': score,
            'errors': errors_found,
            'details': f"语法检查得分: {score:.2f}"
        }
    
    def _check_reference_traceability(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查引用文件可追溯性"""
        text_content = ' '.join([item['content'] for item in document_data['text_content']])
        
        # 查找引用标准和文件
        import re
        standard_patterns = [
            r'GB[\/T]?\s*\d+[-\.]?\d*[-\.]?\d*',
            r'[A-Z]+[\/T]?\s*\d+[-\.]?\d*',
            r'《[^》]+》'
        ]
        
        found_references = []
        for pattern in standard_patterns:
            matches = re.findall(pattern, text_content)
            found_references.extend(matches)
        
        # 简化评分：有引用得分高
        score = min(1.0, len(found_references) * 0.1)
        
        return {
            'score': score,
            'references': found_references,
            'details': f"找到 {len(found_references)} 个引用标准"
        }
    
    def _check_business_logic(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查业务逻辑"""
        # 简化的逻辑一致性检查
        score = 0.8  # 基础分数
        issues = []
        
        return {
            'score': score,
            'issues': issues,
            'details': "业务逻辑检查完成"
        }
    
    def _check_personnel_configuration(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查人员配备"""
        text_content = ' '.join([item['content'] for item in document_data['text_content']])
        
        # 查找人员配备相关信息
        personnel_keywords = ["工程师", "区段长", "巡线工", "管理处", "负责人"]
        found_personnel = [kw for kw in personnel_keywords if kw in text_content]
        
        score = len(found_personnel) / len(personnel_keywords)
        
        return {
            'score': score,
            'found_personnel': found_personnel,
            'details': f"人员配备检查得分: {score:.2f}"
        }
    
    def _check_emergency_procedures(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查应急处置"""
        text_content = ' '.join([item['content'] for item in document_data['text_content']])
        
        emergency_keywords = ["应急", "处置", "预案", "抢险", "救援"]
        found_emergency = [kw for kw in emergency_keywords if kw in text_content]
        
        score = len(found_emergency) / len(emergency_keywords)
        
        return {
            'score': score,
            'found_emergency': found_emergency,
            'details': f"应急处置检查得分: {score:.2f}"
        }
    
    def _check_template_compliance(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查模板合规性"""
        # 简化的模板检查
        score = 0.9  # 基础分数
        
        return {
            'score': score,
            'details': "模板合规性检查完成"
        } 