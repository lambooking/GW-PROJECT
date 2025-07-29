"""
日志配置模块
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: Optional[str] = None,
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "output/logs"
) -> logging.Logger:
    """
    设置日志配置
    
    Args:
        name: 日志器名称，默认为None（根日志器）
        log_level: 日志级别
        log_file: 日志文件名
        log_dir: 日志目录
    
    Returns:
        配置好的日志器
    """
    
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 获取日志器
    logger = logging.getLogger(name)
    
    # 如果已经配置过，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 创建文件处理器（如果指定了文件）
    if log_file:
        file_path = log_path / log_file
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 防止日志向上传播（避免重复输出）
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器
    
    Args:
        name: 日志器名称
    
    Returns:
        日志器实例
    """
    return logging.getLogger(name) 