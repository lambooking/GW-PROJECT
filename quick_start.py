#!/usr/bin/env python3
"""
RAG智能评分系统 - 快速启动脚本
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=".")
        if result.returncode == 0:
            print(f"✅ {description}成功")
            if result.stdout.strip():
                print(result.stdout.strip())
        else:
            print(f"❌ {description}失败:")
            print(result.stderr.strip())
    except Exception as e:
        print(f"❌ 执行失败: {e}")

def main():
    """主函数"""
    print("🎯 RAG智能评分系统 - 快速启动")
    print("="*50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本需要 >= 3.8")
        return
    
    print(f"✅ Python版本: {sys.version}")
    
    # 检查必要文件
    required_files = ["ragcli", "config/rag_config.yaml", "src/core/__init__.py"]
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ 找到文件: {file_path}")
        else:
            print(f"❌ 缺失文件: {file_path}")
            return
    
    # 运行系统测试
    run_command("python -c \"import src.core; print('Core modules OK')\"", "检查核心模块")
    
    # 显示可用命令
    print("\n📋 可用命令:")
    print("  ./ragcli test                    # 测试系统")
    print("  ./ragcli score document.pdf      # 评分文档")
    print("  ./ragcli batch directory/        # 批量评分")
    print("  ./ragcli kb list                 # 知识库管理")
    print("  ./ragcli status                  # 系统状态")
    print("  ./ragcli --help                  # 查看帮助")
    
    print("\n🎉 系统就绪! 开始使用吧!")

if __name__ == "__main__":
    main()
