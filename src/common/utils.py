"""
通用工具函数
"""

import os
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, Any, Union, List
import logging

logger = logging.getLogger(__name__)


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        配置字典
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                return json.load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
    except Exception as e:
        logger.error(f"加载配置文件失败 {config_path}: {e}")
        return {}


def save_config(config: Dict[str, Any], config_path: Union[str, Path]) -> bool:
    """
    保存配置文件
    
    Args:
        config: 配置字典
        config_path: 配置文件路径
    
    Returns:
        是否保存成功
    """
    config_path = Path(config_path)
    
    try:
        # 创建目录
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(config, f, default_flow_style=False, ensure_ascii=False, indent=2)
            elif config_path.suffix.lower() == '.json':
                json.dump(config, f, ensure_ascii=False, indent=2)
            else:
                raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
        
        logger.info(f"配置文件保存成功: {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"保存配置文件失败 {config_path}: {e}")
        return False


def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'md5') -> str:
    """
    计算文件哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 ('md5', 'sha1', 'sha256')
    
    Returns:
        文件哈希值
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def ensure_dir(dir_path: Union[str, Path]) -> Path:
    """
    确保目录存在
    
    Args:
        dir_path: 目录路径
    
    Returns:
        Path对象
    """
    dir_path = Path(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件大小
    """
    return Path(file_path).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        格式化的文件大小字符串
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def validate_file_format(file_path: Union[str, Path], allowed_formats: List[str]) -> bool:
    """
    验证文件格式
    
    Args:
        file_path: 文件路径
        allowed_formats: 允许的文件格式列表
    
    Returns:
        是否为允许的格式
    """
    file_path = Path(file_path)
    return file_path.suffix.lower() in [fmt.lower() for fmt in allowed_formats]


def split_text_by_length(text: str, max_length: int, overlap: int = 0) -> List[str]:
    """
    按长度分割文本
    
    Args:
        text: 输入文本
        max_length: 最大长度
        overlap: 重叠长度
    
    Returns:
        分割后的文本列表
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_length
        chunks.append(text[start:end])
        start = end - overlap if overlap > 0 else end
    
    return chunks


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并多个字典
    
    Args:
        *dicts: 要合并的字典
    
    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result 