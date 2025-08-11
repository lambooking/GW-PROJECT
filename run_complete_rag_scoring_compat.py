#!/usr/bin/env python3
"""
兼容性包装器 - 重定向旧API调用到新架构
"""

import sys
import logging
from pathlib import Path

# 设置基础日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def migrate_notice():
    """显示迁移提示"""
    print("\n" + "="*60)
    print("📢 RAG智能评分系统已升级到新架构!")
    print("="*60)
    print("🔄 正在使用兼容性模式运行...")
    print("💡 建议使用新的CLI工具: ./ragcli")
    print("📖 查看 README_NEW.md 了解新功能")
    print("="*60 + "\n")

class RAGScoringSystemCompat:
    """兼容性包装器类"""
    
    def __init__(self):
        migrate_notice()
        logger.info("初始化兼容性包装器...")
        # 这里可以初始化新系统的相关组件
        
    def score_document_from_file(self, file_path):
        """旧API: 评分单个文档"""
        logger.info(f"评分文档: {file_path}")
        print("⚠️  请使用新CLI: ./ragcli score " + str(file_path))
        return None
        
    def batch_score_documents(self, file_paths):
        """旧API: 批量评分"""
        logger.info(f"批量评分 {len(file_paths)} 个文档")
        print("⚠️  请使用新CLI: ./ragcli batch <directory>")
        return []
        
    def test_vllm_connection(self):
        """旧API: 测试VLLM连接"""
        logger.info("测试VLLM连接")
        print("⚠️  请使用新CLI: ./ragcli test")
        return False

# 创建兼容实例
RAGScoringSystem = RAGScoringSystemCompat

def main():
    """主函数"""
    system = RAGScoringSystem()
    print("✅ 兼容性包装器已加载")
    print("🚀 开始使用新的CLI工具吧!")

if __name__ == "__main__":
    main()
