"""
审核引擎核心类
"""

import time
import logging
from typing import Dict, List, Any
from pathlib import Path

from ..data_processing.document_parser import DocumentParser
from ..models.text_audit_model import InstructionBookAuditor
from ..models.multimodal_audit_model import RiskManagementAuditor
from ..common.utils import load_config

logger = logging.getLogger(__name__)


class AuditEngine:
    """审核引擎主类"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        try:
            self.config = load_config(config_path)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
            self.config = self._get_default_config()
        
        self.document_parser = DocumentParser()
        
        # 初始化审核器
        try:
            self.instruction_auditor = InstructionBookAuditor(
                model_path=self.config.get('models', {}).get('text_audit', {}).get('model_path'),
                tokenizer_name=self.config.get('models', {}).get('text_audit', {}).get('model_name', 'chinese-roberta-wwm-ext')
            )
            
            self.risk_auditor = RiskManagementAuditor(
                model_path=self.config.get('models', {}).get('multimodal_audit', {}).get('model_path'),
                tokenizer_name=self.config.get('models', {}).get('multimodal_audit', {}).get('text_model', 'chinese-roberta-wwm-ext')
            )
        except Exception as e:
            logger.error(f"初始化审核器失败: {e}")
            raise
        
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'models': {
                'text_audit': {
                    'model_name': 'chinese-roberta-wwm-ext',
                    'model_path': None
                },
                'multimodal_audit': {
                    'text_model': 'chinese-roberta-wwm-ext',
                    'model_path': None
                }
            }
        }
        
    def audit_instruction_book(self, file_path: str) -> Dict[str, Any]:
        """审核作业指导书"""
        start_time = time.time()
        
        try:
            # 解析文档
            logger.info(f"开始解析作业指导书: {file_path}")
            document_data = self.document_parser.parse_document(file_path)
            
            # 进行审核
            logger.info("开始审核作业指导书内容")
            audit_results = self.instruction_auditor.audit_document(document_data)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            audit_results['processing_time'] = processing_time
            audit_results['file_path'] = file_path
            audit_results['document_type'] = 'instruction_book'
            
            # 根据处理时间调整效率得分
            if processing_time <= 30:
                efficiency_score = 1.0
            elif processing_time <= 60:
                efficiency_score = 0.8
            elif processing_time <= 120:
                efficiency_score = 0.6
            else:
                efficiency_score = 0.2
            
            audit_results['processing_efficiency'] = {
                'score': efficiency_score,
                'time': processing_time,
                'details': f"处理时间: {processing_time:.2f}秒"
            }
            
            logger.info(f"作业指导书审核完成，总分: {audit_results['overall_score']:.2f}")
            return audit_results
            
        except Exception as e:
            logger.error(f"作业指导书审核失败: {e}")
            return {
                'overall_score': 0.0,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'file_path': file_path,
                'document_type': 'instruction_book'
            }
    
    def audit_risk_management(self, file_path: str) -> Dict[str, Any]:
        """审核高后果区风险管控方案"""
        start_time = time.time()
        
        try:
            # 解析文档
            logger.info(f"开始解析风险管控方案: {file_path}")
            document_data = self.document_parser.parse_document(file_path)
            
            # 进行审核
            logger.info("开始审核风险管控方案内容")
            audit_results = self.risk_auditor.audit_document(document_data)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            audit_results['processing_time'] = processing_time
            audit_results['file_path'] = file_path
            audit_results['document_type'] = 'risk_management'
            
            # 根据处理时间调整效率得分
            if processing_time <= 30:
                efficiency_score = 1.0
            elif processing_time <= 60:
                efficiency_score = 0.8
            elif processing_time <= 120:
                efficiency_score = 0.6
            else:
                efficiency_score = 0.2
            
            if 'processing_efficiency' in audit_results:
                audit_results['processing_efficiency']['score'] = efficiency_score
                audit_results['processing_efficiency']['time'] = processing_time
                audit_results['processing_efficiency']['details'] = f"处理时间: {processing_time:.2f}秒"
            
            logger.info(f"风险管控方案审核完成，总分: {audit_results['overall_score']:.2f}")
            return audit_results
            
        except Exception as e:
            logger.error(f"风险管控方案审核失败: {e}")
            return {
                'overall_score': 0.0,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'file_path': file_path,
                'document_type': 'risk_management'
            }
    
    def batch_audit(self, file_paths: List[str], document_type: str = 'auto') -> List[Dict[str, Any]]:
        """批量审核文档"""
        results = []
        
        for file_path in file_paths:
            try:
                # 自动检测文档类型
                if document_type == 'auto':
                    detected_type = self._detect_document_type(file_path)
                else:
                    detected_type = document_type
                
                # 根据类型进行审核
                if detected_type == 'instruction_book':
                    result = self.audit_instruction_book(file_path)
                elif detected_type == 'risk_management':
                    result = self.audit_risk_management(file_path)
                else:
                    result = {
                        'overall_score': 0.0,
                        'error': f"未知文档类型: {detected_type}",
                        'file_path': file_path
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"批量审核文件 {file_path} 失败: {e}")
                results.append({
                    'overall_score': 0.0,
                    'error': str(e),
                    'file_path': file_path
                })
        
        return results
    
    def _detect_document_type(self, file_path: str) -> str:
        """检测文档类型"""
        file_name = Path(file_path).name.lower()
        
        # 基于文件名的简单检测
        if any(keyword in file_name for keyword in ['作业指导书', 'instruction', '指导书']):
            return 'instruction_book'
        elif any(keyword in file_name for keyword in ['风险管控', '高后果区', 'risk', '管控方案']):
            return 'risk_management'
        else:
            # 如果无法从文件名判断，返回默认类型
            return 'instruction_book'
    
    def get_audit_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算审核统计信息"""
        if not results:
            return {}
        
        # 基础统计
        total_files = len(results)
        successful_audits = len([r for r in results if 'error' not in r])
        failed_audits = total_files - successful_audits
        
        # 分数统计
        scores = [r.get('overall_score', 0) for r in results if 'error' not in r]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 按类型统计
        instruction_books = [r for r in results if r.get('document_type') == 'instruction_book']
        risk_managements = [r for r in results if r.get('document_type') == 'risk_management']
        
        # 处理时间统计
        processing_times = [r.get('processing_time', 0) for r in results if 'processing_time' in r]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        statistics = {
            'total_files': total_files,
            'successful_audits': successful_audits,
            'failed_audits': failed_audits,
            'success_rate': successful_audits / total_files if total_files > 0 else 0,
            'average_score': avg_score,
            'score_distribution': {
                'excellent': len([s for s in scores if s >= 0.9]),
                'good': len([s for s in scores if 0.8 <= s < 0.9]),
                'fair': len([s for s in scores if 0.7 <= s < 0.8]),
                'poor': len([s for s in scores if s < 0.7])
            },
            'document_types': {
                'instruction_books': len(instruction_books),
                'risk_managements': len(risk_managements)
            },
            'average_processing_time': avg_processing_time,
            'efficiency_stats': {
                'fast': len([t for t in processing_times if t <= 30]),
                'normal': len([t for t in processing_times if 30 < t <= 60]),
                'slow': len([t for t in processing_times if t > 60])
            }
        }
        
        return statistics 