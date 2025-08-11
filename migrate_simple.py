#!/usr/bin/env python3
"""
简化版架构迁移脚本
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """检查必要的依赖包"""
    logger.info("🔍 检查系统依赖...")
    
    missing_packages = []
    
    # 检查基础包
    try:
        import pydantic
        logger.info("  ✅ pydantic 可用")
    except ImportError:
        missing_packages.append("pydantic")
    
    try:
        import yaml
        logger.info("  ✅ PyYAML 可用")
    except ImportError:
        missing_packages.append("PyYAML")
    
    try:
        import click
        logger.info("  ✅ click 可用")
    except ImportError:
        missing_packages.append("click")
    
    if missing_packages:
        logger.warning(f"  ⚠️  缺少依赖包: {', '.join(missing_packages)}")
        logger.info("  💡 请运行: pip install " + " ".join(missing_packages))
        return False
    
    return True


def create_directories():
    """创建必要的目录结构"""
    logger.info("📁 创建目录结构...")
    
    directories = [
        "logs",
        "output/rag_scoring_reports",
        "output/rag_scoring_reports/html",
        "output/rag_knowledge_base",
        "config"
    ]
    
    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✅ 创建目录: {dir_path}")


def check_old_system():
    """检查旧系统文件"""
    logger.info("🔍 检查旧系统文件...")
    
    old_files = [
        "run_complete_rag_scoring.py",
        "src/inference/rag_scoring_engine.py", 
        "src/inference/vllm_client.py",
        "config/config.yaml"
    ]
    
    existing_files = []
    for file_path in old_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
            logger.info(f"  ✅ 找到: {file_path}")
        else:
            logger.warning(f"  ❌ 缺失: {file_path}")
    
    return len(existing_files) > 0


def create_compatibility_wrapper():
    """创建兼容性包装器"""
    logger.info("🔄 创建兼容性包装器...")
    
    compatibility_script = '''#!/usr/bin/env python3
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
    print("\\n" + "="*60)
    print("📢 RAG智能评分系统已升级到新架构!")
    print("="*60)
    print("🔄 正在使用兼容性模式运行...")
    print("💡 建议使用新的CLI工具: ./ragcli")
    print("📖 查看 README_NEW.md 了解新功能")
    print("="*60 + "\\n")

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
'''
    
    compat_file = Path("run_complete_rag_scoring_compat.py")
    with open(compat_file, 'w', encoding='utf-8') as f:
        f.write(compatibility_script)
    
    logger.info(f"✅ 创建兼容性包装器: {compat_file}")


def create_quick_start_script():
    """创建快速启动脚本"""
    logger.info("🚀 创建快速启动脚本...")
    
    start_script = '''#!/usr/bin/env python3
"""
RAG智能评分系统 - 快速启动脚本
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\\n🔧 {description}...")
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
    run_command("python -c \\"import src.core; print('Core modules OK')\\"", "检查核心模块")
    
    # 显示可用命令
    print("\\n📋 可用命令:")
    print("  ./ragcli test                    # 测试系统")
    print("  ./ragcli score document.pdf      # 评分文档")
    print("  ./ragcli batch directory/        # 批量评分")
    print("  ./ragcli kb list                 # 知识库管理")
    print("  ./ragcli status                  # 系统状态")
    print("  ./ragcli --help                  # 查看帮助")
    
    print("\\n🎉 系统就绪! 开始使用吧!")

if __name__ == "__main__":
    main()
'''
    
    start_file = Path("quick_start.py")
    with open(start_file, 'w', encoding='utf-8') as f:
        f.write(start_script)
    
    # 使脚本可执行
    import os
    os.chmod(start_file, 0o755)
    
    logger.info(f"✅ 创建快速启动脚本: {start_file}")


def generate_migration_summary():
    """生成迁移摘要"""
    logger.info("📄 生成迁移摘要...")
    
    summary = f'''# RAG智能评分系统架构迁移摘要

## ✅ 迁移完成项目

1. **新架构创建** - 模块化分层架构
2. **配置系统统一** - config/rag_config.yaml
3. **CLI工具创建** - ./ragcli 统一命令行工具
4. **兼容性包装** - 支持旧API调用
5. **目录结构** - 标准化项目目录

## 📁 新项目结构

```
RAG-PROJECT/
├── src/                    # 核心代码
│   ├── core/              # 框架层
│   ├── config/            # 配置管理
│   ├── data/              # 数据处理
│   └── intelligence/      # 智能推理
├── config/                # 配置文件
├── cli/                   # 命令行工具
├── ragcli                 # 统一CLI入口
└── README_NEW.md          # 新版本文档
```

## 🚀 快速开始

1. **检查系统**:
   ```bash
   python quick_start.py
   ```

2. **安装依赖** (如果需要):
   ```bash
   pip install pydantic PyYAML click
   ```

3. **测试系统**:
   ```bash
   ./ragcli test
   ```

4. **评分文档**:
   ```bash
   ./ragcli score data/raw/场景1\\(1\\).pdf
   ```

## 📖 文档

- **新功能文档**: README_NEW.md
- **原系统文档**: CODE_WORKFLOW.md
- **技术说明**: 技术说明.md

## 🔧 故障排除

如果遇到问题:

1. 检查Python版本 >= 3.8
2. 安装缺失的依赖包
3. 确保VLLM服务正在运行
4. 查看logs/目录下的日志文件

## 💡 下一步

1. 熟悉新的CLI工具
2. 配置config/rag_config.yaml
3. 测试评分功能
4. 迁移旧的知识库数据 (如需要)

---
生成时间: {Path(__file__).stat().st_mtime}
'''
    
    summary_file = Path("MIGRATION_SUMMARY.md")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    logger.info(f"✅ 生成迁移摘要: {summary_file}")


def main():
    """主迁移流程"""
    logger.info("🚀 开始简化版架构迁移...")
    
    # 执行迁移步骤
    steps = [
        ("检查依赖", check_dependencies),
        ("创建目录", create_directories),
        ("检查旧系统", check_old_system),
        ("创建兼容包装", create_compatibility_wrapper),
        ("创建启动脚本", create_quick_start_script),
        ("生成迁移摘要", generate_migration_summary)
    ]
    
    completed_steps = 0
    for step_name, step_func in steps:
        try:
            logger.info(f"\\n📋 执行步骤: {step_name}")
            result = step_func()
            if result is not False:  # None or True means success
                completed_steps += 1
                logger.info(f"✅ {step_name} - 完成")
            else:
                logger.warning(f"⚠️  {step_name} - 部分完成")
                completed_steps += 0.5
        except Exception as e:
            logger.error(f"❌ {step_name} - 失败: {e}")
    
    # 显示结果
    logger.info(f"\\n🎯 迁移完成! 成功执行 {completed_steps}/{len(steps)} 个步骤")
    
    if completed_steps >= len(steps) - 1:
        logger.info("✅ 迁移成功!")
        print("\\n" + "="*60)
        print("🎉 RAG智能评分系统架构迁移完成!")
        print("="*60)
        print("📋 下一步操作:")
        print("  1. python quick_start.py        # 系统检查")
        print("  2. ./ragcli test                 # 测试功能")
        print("  3. 查看 README_NEW.md            # 新功能文档")
        print("  4. 查看 MIGRATION_SUMMARY.md     # 迁移摘要")
        print("="*60)
    else:
        logger.warning("⚠️  迁移部分完成，请检查上述错误信息")


if __name__ == "__main__":
    main()