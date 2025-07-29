#!/usr/bin/env python3
"""
启动AI审核系统服务器
"""

import sys
import os
from pathlib import Path
import argparse
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.common.logger import setup_logger


def main():
    parser = argparse.ArgumentParser(description='启动AI审核系统服务器')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    parser.add_argument('--workers', type=int, default=1, help='工作进程数')
    parser.add_argument('--reload', action='store_true', help='开启自动重载')
    parser.add_argument('--log-level', type=str, default='info', help='日志级别')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logger(log_level=args.log_level.upper())
    logger = logging.getLogger(__name__)
    
    # 创建必要的目录
    for dir_path in ['output/logs', 'output/reports', 'data/raw']:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 50)
    logger.info("🚀 启动生产运维管理AI审核系统")
    logger.info("=" * 50)
    logger.info(f"📍 服务地址: http://{args.host}:{args.port}")
    logger.info(f"📖 API文档: http://{args.host}:{args.port}/docs")
    logger.info(f"📋 ReDoc: http://{args.host}:{args.port}/redoc")
    logger.info("=" * 50)
    
    try:
        import uvicorn
        from src.api.app import app
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            workers=args.workers,
            reload=args.reload,
            log_level=args.log_level
        )
    except ImportError as e:
        logger.error(f"缺少依赖: {e}")
        logger.error("请运行: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动服务器失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 