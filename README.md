# RAG智能评分系统

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![RAG Technology](https://img.shields.io/badge/RAG-Enabled-green.svg)](README.md)
[![Architecture](https://img.shields.io/badge/architecture-modular-blue.svg)](docs/README_NEW.md)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 项目简介

RAG智能评分系统是一个基于检索增强生成(RAG)技术的文档智能评分系统，专门用于对作业指导书和高后果区风险管控方案进行自动化评估和评分。系统采用现代化的模块化架构，集成VLLM推理引擎和向量知识库，实现高效、准确的文档审核。

### 🔥 核心特性

- 📄 **作业指导书评分**: 基于RAG技术的智能评估，覆盖结构、内容、合规性检查
- 🏗️ **风险管控方案评分**: 多模态分析，支持图像识别和文本理解
- 🤖 **RAG增强**: 集成向量知识库，提供上下文感知的智能评分
- 📊 **智能报告**: 自动生成HTML和JSON格式的详细评分报告
- 🚀 **批量处理**: 支持大规模文档批量评分和处理
- 🔧 **模块化架构**: 插件式设计，易于扩展和维护

### 🎯 技术亮点

- ✅ **VLLM集成**: 高性能大语言模型推理引擎
- 🧠 **知识库驱动**: ChromaDB向量数据库支持检索增强
- ⚡ **高效处理**: 单份文档评分时间≤120秒
- 🔄 **脚本化**: 提供完整的Python脚本接口
- 📱 **API接口**: RESTful API支持集成部署
- 🛡️ **信创兼容**: 支持信创环境和开源模型部署

## 🚀 快速开始

### 📋 环境要求

- Python 3.9+
- 8GB+ RAM (推荐16GB+)
- VLLM服务 (用于大语言模型推理)
- ChromaDB (可选，用于向量知识库)

### ⚙️ 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd GW-PROJECT
```

2. **安装依赖**
```bash
pip install -r requirements.txt

# 可选：安装向量数据库支持
pip install chromadb sentence-transformers
```

3. **配置系统**
```bash
# 配置文件已预置，可根据需要修改
vim config/rag_config.yaml
```

4. **启动VLLM服务**
```bash
# 启动VLLM推理服务
bash scripts/start_vllm.sh
```

5. **初始化系统**
```bash
# 使用统一CLI工具初始化
./ragcli init

# 或使用Python脚本
python rag_scoring_system.py --help
```

### 💡 使用示例

#### 统一CLI工具

```bash
# 查看所有可用命令
./ragcli --help

# 单文档评分
./ragcli score document.docx --type instruction_book

# 批量评分
./ragcli batch ./documents/ --output ./results/

# 启动知识库管理
./ragcli kb --index ./knowledge_docs/

# 生成HTML报告
./ragcli report --input result.json --format html
```

#### Python API使用

```python
from src.core import RAGScoringApplication
from src.config import ConfigManager

# 创建应用实例
config = ConfigManager("config/rag_config.yaml")
app = RAGScoringApplication(config)

# 评分单个文档
result = app.score_document("document.docx", "instruction_book")
print(f"评分结果: {result.overall_score:.2f}")

# 批量评分
results = app.batch_score("./documents/", output_dir="./results/")
```

#### 完整评分流程

```bash
# 1. 启动VLLM服务
bash scripts/start_vllm.sh

# 2. 初始化知识库
./ragcli kb --build

# 3. 运行评分
python run_complete_rag_scoring.py document.docx instruction_book

# 4. 查看结果
ls output/rag_scoring_reports/
```

## 📁 项目结构

```
GW-PROJECT/
├── src/                        # 🏗️ 核心源码 (模块化架构)
│   ├── core/                   # 核心应用框架
│   ├── config/                 # 配置管理系统
│   ├── data/                   # 数据处理层
│   │   ├── parsers/            # 文档解析器
│   │   └── processors/         # 数据处理器
│   ├── intelligence/           # 🧠 智能推理层
│   │   ├── engines/            # RAG评分引擎
│   │   ├── knowledge/          # 知识库管理
│   │   └── clients/            # VLLM客户端
│   ├── inference/              # 推理与评分
│   ├── services/               # 业务服务层
│   ├── api/                    # RESTful API
│   └── utils/                  # 工具和报告生成
├── config/                     # ⚙️ 配置文件
│   └── rag_config.yaml         # 主配置文件
├── cli/                        # 🔧 命令行工具
├── scripts/                    # 📜 实用脚本
│   └── start_vllm.sh          # VLLM启动脚本
├── docs/                       # 📚 详细文档
│   ├── README_NEW.md          # 重构架构说明
│   ├── CODE_WORKFLOW.md       # 代码工作流
│   └── 技术路线.md            # 技术实施路线
├── output/                     # 📊 输出目录
│   ├── rag_scoring_reports/   # 评分报告
│   └── rag_knowledge_base/    # 向量知识库
├── data/                       # 🗂️ 数据目录
├── logs/                       # 📋 日志文件
├── ragcli                      # 🚀 统一CLI入口
├── rag_scoring_system.py       # 主应用入口
└── requirements.txt            # Python依赖
```

## 📖 文档资源

### 详细文档
- 📘 [重构架构说明](docs/README_NEW.md) - 模块化架构详细介绍
- 🔄 [代码工作流程](docs/CODE_WORKFLOW.md) - 系统工作流程详解
- 🛠️ [技术实施路线](docs/技术路线.md) - 技术方案和实现路径
- 📋 [项目详细说明](docs/说明.md) - 完整的项目需求和规格
- ⚡ [重构完成报告](docs/REFACTORING_COMPLETED.md) - 架构升级总结

### API接口

RAG评分系统提供RESTful API接口：

| 功能 | 入口文件 | 描述 |
|------|----------|------|
| 完整评分 | `run_complete_rag_scoring.py` | 主要评分入口 |
| 兼容模式 | `run_complete_rag_scoring_compat.py` | 兼容性入口 |
| 快速评分 | `rag_scoring_system.py` | 重构版入口 |
| CLI工具 | `ragcli` | 统一命令行界面 |

## ⚙️ 配置说明

### 主配置文件 (config/rag_config.yaml)

```yaml
# 系统配置
system:
  debug: false
  log_level: "INFO"
  max_workers: 4
  timeout: 120

# VLLM服务配置
vllm:
  host: "localhost"
  port: 8000
  model_name: "qwen2.5-vl-3b"
  max_tokens: 2048
  temperature: 0.1

# 知识库配置
knowledge_base:
  storage_type: "chromadb"
  storage_path: "output/rag_knowledge_base"
  embedding_model: "all-MiniLM-L6-v2"
  chunk_size: 1000
  chunk_overlap: 200

# 文档处理配置
processing:
  supported_formats: [".pdf", ".docx", ".doc"]
  max_file_size_mb: 50
  ocr_enabled: true
  image_extraction: true
```

## 🔧 开发指南

### 架构扩展

1. **添加新评分引擎**
   ```bash
   # 在 src/intelligence/engines/ 中实现新引擎
   # 使用工厂模式注册到 ScoringEngineFactory
   ```

2. **扩展文档解析器**
   ```bash
   # 在 src/data/parsers/ 中添加新解析器
   # 继承 BaseDocumentParser 基类
   ```

3. **添加新知识库类型**
   ```bash
   # 在 src/intelligence/knowledge/ 中实现
   # 遵循 KnowledgeBase 接口规范
   ```

### 部署指南

```bash
# 1. 准备VLLM服务
bash scripts/start_vllm.sh

# 2. 启动API服务  
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# 3. 或使用统一入口
python rag_scoring_system.py

# 4. 批量处理
python run_complete_rag_scoring.py --batch ./documents/
```

## 🚀 性能优化

### VLLM优化
- 调整 `max_tokens` 和 `temperature` 参数
- 根据GPU内存调整批处理大小
- 使用tensor parallelism提升推理速度

### 知识库优化
- 调整chunk_size和chunk_overlap参数
- 选择合适的embedding模型
- 定期更新和清理向量库

### 系统监控
- 日志位置: `logs/rag_scoring_system.log`
- 报告输出: `output/rag_scoring_reports/`
- 性能指标: 120秒内完成单文档评分

## ❓ 常见问题

### Q: VLLM服务启动失败怎么办？
**A**: 检查以下几点：
- 确保GPU内存充足（推荐8GB+）
- 检查模型路径是否正确
- 查看 `scripts/start_vllm.sh` 中的配置参数

### Q: 如何提高评分准确率？
**A**: 可以通过以下方式优化：
- 扩充知识库内容，提供更多参考文档
- 调整VLLM的temperature参数（降低随机性）
- 优化prompt工程，提供更精确的指令

### Q: 支持哪些文档格式？
**A**: 当前支持：
- Microsoft Word (.docx, .doc)
- PDF (.pdf)
- 支持OCR和图像提取

### Q: 如何进行批量评分？
**A**: 使用以下方式：
```bash
# CLI方式
./ragcli batch ./documents/ --output ./results/

# Python脚本方式  
python run_complete_rag_scoring.py --batch ./documents/
```

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 参与贡献

本项目是RAG智能评分系统的开源实现，欢迎：
- 🐛 提交Bug报告和功能建议
- 🔧 贡献代码和文档改进
- 📚 完善知识库和测试用例

---

> **项目说明**: 这是一个基于RAG技术的AI文档评分系统，专为生产运维管理领域文档审核而设计。系统采用模块化架构，集成VLLM推理引擎，支持高效、准确的文档质量评估。