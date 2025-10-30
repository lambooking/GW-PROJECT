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
- 🛡️ **信创兼容**: 支持信创环境和开源模型部署(待开发)

## 🚀 快速开始

### 📋 环境要求

- Python 3.9+
- 8GB+ RAM (推荐16GB+)
- VLLM服务 (用于大语言模型推理)(24g 最低)
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

## 📖 使用 run_complete_rag_scoring.py 评分多格式文档

系统支持 **PDF**、**DOCX**、**DOC** 三种文档格式的智能评分。

### 🎯 快速使用

```bash
# 测试系统连接
python run_complete_rag_scoring.py test

# 评分 PDF 文件
python run_complete_rag_scoring.py score data/raw/场景1\(1\).pdf

# 评分 DOCX 文件
python run_complete_rag_scoring.py score documents/instruction.docx

# 评分 DOC 文件（需要安装 antiword）
python run_complete_rag_scoring.py score documents/legacy.doc

# 批量评分目录中的所有 PDF 文件
python run_complete_rag_scoring.py batch data/raw/
```

### 📋 支持的格式

| 格式 | 解析引擎 | 支持功能 | 备注 |
|------|---------|---------|------|
| **PDF** | PyMuPDF | 文本、表格、图片 | 推荐用于扫描文档 |
| **DOCX** | python-docx | 段落、表格、图片、样式 | 推荐用于 Word 编辑文档 |
| **DOC** | antiword | 文本提取 | 需安装 antiword 工具 |

### 📊 输出结果

评分完成后会生成两种格式的报告：

- **JSON 报告**: `output/rag_scoring_reports/rag_scoring_report_<文档名>_<时间>.json`
- **HTML 报告**: `output/rag_scoring_reports/html/rag_scoring_report_<文档名>_<时间>.html`

### 📚 详细使用指南

完整的使用说明、命令详解、常见问题和最佳实践，请参阅：

👉 **[详细使用指南 (USAGE_GUIDE.md)](docs/USAGE_GUIDE.md)**

包含内容：
- ✅ 各格式详细说明和能力对比
- ✅ 完整的命令行参数说明
- ✅ 丰富的使用示例和场景
- ✅ 常见问题排查和解决方案
- ✅ 最佳实践和性能优化建议

## 🗂️ 批量目录审核

系统支持对整个目录树进行批量智能评分，自动处理多层级目录结构中的所有文档。

### 🎯 核心特性

- **递归目录扫描**: 自动识别所有子目录中的文档文件
- **目录结构映射**: 输出目录完全保持输入目录结构
- **多格式报告**: 为每个文档生成JSON和HTML详细报告
- **分层级统计**: 提供总体和子目录级别的汇总分析
- **可视化汇总**: 生成美观的HTML汇总报告，包含图表和统计

### 🚀 快速使用

```bash
# 基本用法：批量评分整个目录
python run_batch_rag_scoring.py <输入目录> [输出目录]

# 示例：使用默认输出目录
python run_batch_rag_scoring.py /path/to/documents

# 示例：指定自定义输出目录
python run_batch_rag_scoring.py /path/to/documents output/my_results
```

### 📂 目录结构示例

**输入目录**:
```
提交训练集/
├── 一区一案/
│   ├── 文档1.docx
│   ├── 文档2.pdf
│   └── 文档3.docx
└── 作业指导书/
    ├── 文档4.pdf
    └── 文档5.docx
```

**输出目录** (保持相同结构):
```
output/batch_rag_scoring/
├── 一区一案/
│   ├── 文档1_report_20250130_143022.json
│   ├── 文档1_report_20250130_143022.html
│   ├── 文档2_report_20250130_143155.json
│   └── ...
├── 作业指导书/
│   ├── 文档4_report_20250130_143320.json
│   └── ...
├── batch_summary_20250130_143500.json    # JSON汇总报告
├── batch_summary_20250130_143500.txt     # 文本汇总报告
└── batch_summary_20250130_143500.html    # HTML汇总报告
```

### 📊 汇总报告内容

批量评分完成后，系统会生成包含以下内容的汇总报告：

- **总体统计**: 总文件数、成功率、平均分数、最高/最低分
- **子目录统计**: 每个子文件夹的独立统计分析
- **评分分布**: 分数段分布、等级分布
- **处理详情**: 成功/失败清单、耗时分析
- **可视化图表**: 子目录对比、分数分布、等级分布

### 📖 详细文档

完整的批量审核使用说明，请参阅：

👉 **[批量审核使用指南 (BATCH_SCORING_GUIDE.md)](docs/BATCH_SCORING_GUIDE.md)**

包含内容：
- ✅ 详细的功能说明和使用步骤
- ✅ 目录结构组织最佳实践
- ✅ 汇总报告解读指南
- ✅ 常见问题和故障排除
- ✅ 高级用法和性能优化

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
- 📖 [使用指南](docs/USAGE_GUIDE.md) - 多格式文档评分完整使用指南 ⭐ **推荐阅读**
- 🗂️ [批量审核指南](docs/BATCH_SCORING_GUIDE.md) - 批量目录审核完整使用指南 ⭐ **新功能**
- 🖋️ [签字页优化说明](docs/SIGNATURE_OPTIMIZATION.md) - DOCX签字页处理性能优化 ⚡ **性能提升67%**
- 🔄 [代码工作流程](docs/CODE_WORKFLOW.md) - 系统工作流程详解
- 🛠️ [技术实施路线](docs/技术路线.md) - 技术方案和实现路径
- 📋 [项目详细说明](docs/说明.md) - 完整的项目需求和规格
- ⚡ [重构完成报告](docs/REFACTORING_COMPLETED.md) - 架构升级总结

### API接口

RAG评分系统提供多种评分入口：

| 功能 | 入口文件 | 描述 |
|------|----------|------|
| 完整评分 | `run_complete_rag_scoring.py` | 单文档评分主入口 |
| 批量目录审核 | `run_batch_rag_scoring.py` | 批量目录评分入口 ⭐ **新增** |
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
**A**: 系统提供专门的批量目录审核功能：
```bash
# 批量目录审核（推荐）- 保持目录结构
python run_batch_rag_scoring.py /path/to/documents

# 指定输出目录
python run_batch_rag_scoring.py /path/to/documents output/my_results

# CLI方式
./ragcli batch ./documents/ --output ./results/

# 批量评分单个目录中的所有PDF
python run_complete_rag_scoring.py batch ./documents/
```

详细使用说明请参阅 [批量审核指南](docs/BATCH_SCORING_GUIDE.md)

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 参与贡献

本项目是RAG智能评分系统的开源实现，欢迎：
- 🐛 提交Bug报告和功能建议
- 🔧 贡献代码和文档改进
- 📚 完善知识库和测试用例

---

> **项目说明**: 这是一个基于RAG技术的AI文档评分系统，专为生产运维管理领域文档审核而设计。系统采用模块化架构，集成VLLM推理引擎，支持高效、准确的文档质量评估。