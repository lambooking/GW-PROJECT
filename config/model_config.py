"""
模型配置管理
"""

from dataclasses import dataclass
from typing import Dict, List, Any
import yaml
from pathlib import Path


@dataclass
class TextAuditConfig:
    """文本审核模型配置"""
    model_name: str = "chinese-roberta-wwm-ext"
    max_length: int = 512
    batch_size: int = 16
    learning_rate: float = 2e-5
    epochs: int = 10
    model_path: str = None


@dataclass
class MultiModalConfig:
    """多模态审核模型配置"""
    vision_model: str = "chinese-clip-vit-base-patch16"
    text_model: str = "chinese-roberta-wwm-ext"
    fusion_dim: int = 768
    dropout: float = 0.1
    model_path: str = None


@dataclass
class SignatureDetectionConfig:
    """签名检测配置"""
    model_path: str = "models/signature_detector.pth"
    confidence_threshold: float = 0.8


@dataclass
class LayoutAnalysisConfig:
    """版面分析配置"""
    model_path: str = "models/layout_analyzer.pth"
    classes: List[str] = None
    
    def __post_init__(self):
        if self.classes is None:
            self.classes = ["text", "image", "table", "title"]


class ModelConfig:
    """模型配置管理器"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()
        
        # 初始化各模型配置
        self.text_audit = TextAuditConfig(**self._config.get('models', {}).get('text_audit', {}))
        self.multimodal_audit = MultiModalConfig(**self._config.get('models', {}).get('multimodal_audit', {}))
        self.signature_detection = SignatureDetectionConfig(**self._config.get('models', {}).get('signature_detection', {}))
        self.layout_analysis = LayoutAnalysisConfig(**self._config.get('models', {}).get('layout_analysis', {}))
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path.exists():
            return {}
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_audit_rules(self, document_type: str) -> Dict[str, Any]:
        """获取审核规则配置"""
        return self._config.get('audit_rules', {}).get(document_type, {})
    
    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return self._config.get('system', {})
    
    def get_data_processing_config(self) -> Dict[str, Any]:
        """获取数据处理配置"""
        return self._config.get('data_processing', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self._config.get('api', {}) 