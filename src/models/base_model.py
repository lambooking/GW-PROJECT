"""
基础模型抽象类
"""

from abc import ABC, abstractmethod
import torch
import torch.nn as nn
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseModel(ABC, nn.Module):
    """基础模型抽象类"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    @abstractmethod
    def forward(self, *args, **kwargs):
        """前向传播"""
        pass
    
    @abstractmethod
    def predict(self, *args, **kwargs) -> Dict[str, Any]:
        """预测接口"""
        pass
    
    def save_model(self, save_path: str) -> bool:
        """
        保存模型
        
        Args:
            save_path: 保存路径
            
        Returns:
            是否保存成功
        """
        try:
            torch.save({
                'model_state_dict': self.state_dict(),
                'config': self.config,
                'model_class': self.__class__.__name__
            }, save_path)
            logger.info(f"模型保存成功: {save_path}")
            return True
        except Exception as e:
            logger.error(f"模型保存失败: {e}")
            return False
    
    def load_model(self, load_path: str) -> bool:
        """
        加载模型
        
        Args:
            load_path: 模型路径
            
        Returns:
            是否加载成功
        """
        try:
            checkpoint = torch.load(load_path, map_location=self.device)
            self.load_state_dict(checkpoint['model_state_dict'])
            logger.info(f"模型加载成功: {load_path}")
            return True
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        
        return {
            'model_class': self.__class__.__name__,
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'device': str(self.device),
            'config': self.config
        }
    
    def freeze_parameters(self, module_names: Optional[list] = None):
        """
        冻结参数
        
        Args:
            module_names: 要冻结的模块名称列表，如果为None则冻结所有参数
        """
        if module_names is None:
            for param in self.parameters():
                param.requires_grad = False
        else:
            for name, module in self.named_modules():
                if any(module_name in name for module_name in module_names):
                    for param in module.parameters():
                        param.requires_grad = False
    
    def unfreeze_parameters(self, module_names: Optional[list] = None):
        """
        解冻参数
        
        Args:
            module_names: 要解冻的模块名称列表，如果为None则解冻所有参数
        """
        if module_names is None:
            for param in self.parameters():
                param.requires_grad = True
        else:
            for name, module in self.named_modules():
                if any(module_name in name for module_name in module_names):
                    for param in module.parameters():
                        param.requires_grad = True 