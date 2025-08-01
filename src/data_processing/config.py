"""
数据预处理配置模块
"""

from typing import Dict, Any
import logging

class PreprocessingConfig:
    """数据预处理配置类"""
    
    def __init__(self):
        # 基础配置
        self.debug_mode = False
        self.max_processing_time = 120  # 最大处理时间（秒）
        self.enable_ocr = True
        self.enable_enhanced_pdf = True
        
        # 文档分类配置
        self.classification_confidence_threshold = 0.7
        
        # OCR配置
        self.ocr_config = {
            'use_angle_cls': True,
            'lang': 'ch',
            'det_db_thresh': 0.3,
            'det_db_box_thresh': 0.6,
            'det_db_unclip_ratio': 1.5,
            'use_dilation': False,
            'det_db_score_mode': 'fast',
            'rec_batch_num': 6
        }
        
        # 实体提取配置
        self.entity_extraction_config = {
            'enable_date_validation': True,
            'enable_technical_validation': True,
            'enable_personnel_validation': True,
            'confidence_threshold': 0.6
        }
        
        # 多模态融合配置
        self.fusion_config = {
            'cross_modal_similarity_threshold': 0.6,
            'enable_semantic_linking': True,
            'max_image_size': 10 * 1024 * 1024,  # 10MB
        }
        
        # 性能配置
        self.performance_config = {
            'max_text_length': 1000000,  # 最大文本长度
            'max_table_size': 1000,      # 最大表格大小
            'max_images': 50,            # 最大图片数量
            'timeout_per_step': 30       # 每步最大超时时间
        }
        
        # 日志配置
        self.logging_config = {
            'level': logging.INFO,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'enable_file_logging': True,
            'log_file_path': 'logs/preprocessing.log'
        }
        
        # 输出配置
        self.output_config = {
            'save_intermediate_results': True,
            'output_format': 'json',
            'include_raw_data': False,  # 是否包含原始数据（调试用）
            'enable_quality_assessment': True
        }
        
        # 场景特定配置
        self.scenario_configs = {
            'scenario_one': {
                'required_sections': [
                    'scope', 'responsibilities', 'work_procedures',
                    'emergency_procedures', 'safety_requirements', 'training'
                ],
                'technical_param_validation': True,
                'personnel_ratio_validation': True
            },
            'scenario_two': {
                'required_diagrams': [
                    'hca_image', 'site_image', 'entry_route', 'escape_route'
                ],
                'temporal_logic_validation': True,
                'cross_modal_validation': True,
                'spatial_reasoning': True
            }
        }
    
    def get_config_dict(self) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            'debug_mode': self.debug_mode,
            'max_processing_time': self.max_processing_time,
            'enable_ocr': self.enable_ocr,
            'enable_enhanced_pdf': self.enable_enhanced_pdf,
            'classification_confidence_threshold': self.classification_confidence_threshold,
            'ocr_config': self.ocr_config,
            'entity_extraction_config': self.entity_extraction_config,
            'fusion_config': self.fusion_config,
            'performance_config': self.performance_config,
            'logging_config': self.logging_config,
            'output_config': self.output_config,
            'scenario_configs': self.scenario_configs
        }
    
    def update_config(self, updates: Dict[str, Any]):
        """更新配置"""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def setup_logging(self):
        """设置日志"""
        import os
        
        # 创建日志目录
        log_dir = os.path.dirname(self.logging_config['log_file_path'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 配置日志
        logging.basicConfig(
            level=self.logging_config['level'],
            format=self.logging_config['format'],
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.logging_config['log_file_path']) if self.logging_config['enable_file_logging'] else logging.NullHandler()
            ]
        )

# 默认配置实例
default_config = PreprocessingConfig()