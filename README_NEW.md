# RAG智能评分系统 - 重构版

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Architecture](https://img.shields.io/badge/architecture-modular-green.svg)](README_NEW.md)
[![Status](https://img.shields.io/badge/status-refactored-success.svg)](README_NEW.md)

## 🎯 项目简介

RAG智能评分系统是一个基于检索增强生成(RAG)技术的文档智能评分系统，专门用于对作业指导书和高后果区风险管控方案进行自动化评估和评分。

### 🔄 重构亮点

- **模块化架构**: 清晰的层次结构，职责明确分离
- **统一配置管理**: 集中化配置系统，支持环境变量覆盖  
- **插件式组件**: 支持动态注册解析器、评分引擎、报告生成器
- **完善的错误处理**: 统一异常体系和错误恢复机制
- **标准化接口**: 一致的API设计和数据结构
- **命令行工具**: 功能丰富的CLI界面

## 📁 项目结构

```
RAG-PROJECT/
├── src/                          # 核心源码目录
│   ├── core/                     # 核心框架层
│   │   ├── application.py        # 主应用程序类
│   │   ├── interfaces.py         # 抽象接口定义
│   │   └── exceptions.py         # 异常定义
│   ├── config/                   # 配置管理系统
│   │   ├── manager.py            # 配置管理器
│   │   └── schemas.py            # 配置数据结构
│   ├── data/                     # 数据处理层
│   │   ├── schemas.py            # 数据结构定义
│   │   ├── parsers/              # 文档解析器
│   │   └── processors/           # 数据处理器
│   ├── intelligence/             # 智能推理层
│   │   ├── engines/              # 评分引擎
│   │   ├── knowledge/            # 知识库管理
│   │   └── clients/              # 外部服务客户端
│   └── services/                 # 业务服务层
├── config/                       # 配置文件
│   └── rag_config.yaml          # 主配置文件
├── cli/                         # 命令行工具
│   └── commands.py              # CLI命令实现
├── ragcli                       # 统一CLI入口
├── rag_scoring_system.py        # 新主入口文件
├── migrate_to_new_architecture.py # 架构迁移脚本
└── requirements.txt             # 依赖包列表
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <project-url>
cd GW-PROJECT

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置系统

```bash
# 复制配置文件
cp config/rag_config.yaml config/local_config.yaml

# 编辑配置文件
vim config/local_config.yaml
```

关键配置项：
```yaml
# VLLM服务配置
vllm:
  host: "localhost"
  port: 8000
  model_name: "qwen2.5-vl-3b"

# 知识库配置  
knowledge_base:
  storage_path: "output/rag_knowledge_base"
  embedding_model: "all-MiniLM-L6-v2"
```

### 3. 启动VLLM服务

```bash
# 启动VLLM服务
bash scripts/start_vllm.sh
```

### 4. 测试系统

```bash
# 使用新CLI工具测试
./ragcli test

# 或使用Python方式
python rag_scoring_system.py test
```

## 💻 使用方法

### CLI工具使用

RAG智能评分系统提供了功能丰富的命令行工具：

```bash
# 评分单个文档
./ragcli score data/raw/场景1\(1\).pdf

# 批量评分
./ragcli batch data/raw/ --pattern "*.pdf,*.docx"

# 知识库管理
./ragcli kb add data/raw/场景1\(1\).pdf
./ragcli kb list
./ragcli kb query "管道巡检"

# 系统状态
./ragcli status
```

### Python API使用

```python
from src.core import RAGScoringApplication
from src.config import ConfigManager

# 创建应用
config = ConfigManager("config/rag_config.yaml")  
app = RAGScoringApplication(config)

# 评分文档
result = app.process_document_complete("path/to/document.pdf")
print(f"评分结果: {result['scoring_result'].total_score}")
```

### 主要命令详解

#### 1. 文档评分

```bash
# 基础评分
./ragcli score document.pdf

# 指定输出目录和格式
./ragcli score document.pdf --output-dir reports --format html,json

# 使用特定评分引擎
./ragcli score document.pdf --engine rag
```

#### 2. 批量处理

```bash  
# 批量评分目录下所有PDF
./ragcli batch documents/

# 自定义匹配模式
./ragcli batch documents/ --pattern "*.pdf,*.docx" 

# 并行处理（未来版本）
./ragcli batch documents/ --parallel
```

#### 3. 知识库管理

```bash
# 添加文档到知识库
./ragcli kb add document.pdf --metadata '{"category": "instruction"}'

# 列出知识库文档
./ragcli kb list --format json

# 查询知识库
./ragcli kb query "安全操作" --top-k 10

# 清空知识库  
./ragcli kb clear
```

## 🏗️ 架构设计

### 层次架构

```
┌─────────────────────────────────────┐
│             CLI Layer               │  # 命令行接口层
├─────────────────────────────────────┤
│          Application Layer          │  # 应用程序层  
├─────────────────────────────────────┤
│           Service Layer             │  # 业务服务层
├─────────────────────────────────────┤
│         Intelligence Layer          │  # 智能推理层
├─────────────────────────────────────┤
│            Data Layer               │  # 数据处理层
├─────────────────────────────────────┤
│             Core Layer              │  # 核心框架层
└─────────────────────────────────────┘
```

### 核心组件

1. **核心框架层 (Core)**
   - `RAGScoringApplication`: 主应用程序类
   - 抽象接口定义 (`DocumentParser`, `ScoringEngine`, etc.)
   - 统一异常处理机制

2. **配置管理 (Config)**
   - `ConfigManager`: 统一配置管理器
   - 支持YAML配置文件和环境变量
   - 配置验证和默认值设定

3. **数据处理层 (Data)**
   - `DocumentParserFactory`: 文档解析器工厂
   - `DocumentProcessorPipeline`: 处理流水线
   - 标准化数据结构 (`StandardizedDocument`)

4. **智能推理层 (Intelligence)**
   - `RAGScoringEngine`: RAG评分引擎
   - `KnowledgeBaseManager`: 知识库管理器
   - `VLLMClient`: VLLM服务客户端

### 设计模式

- **工厂模式**: 解析器和评分引擎创建
- **策略模式**: 多种评分策略支持
- **观察者模式**: 事件驱动架构
- **依赖注入**: 组件间松耦合

## 📊 评分机制

### 场景一：作业指导书评分

| 评分项 | 权重 | 最大分值 | 描述 |
|--------|------|----------|------|
| 结构完整性 | 20% | 20分 | 文档结构和目录完整性 |
| 内容完整性 | 30% | 30分 | 内容完整性和准确性 |
| 引用文件可追溯性 | 15% | 15分 | 引用文件真实性和有效性 |
| 业务逻辑 | 20% | 20分 | 业务流程逻辑合理性 |
| 语法语句 | 15% | 15分 | 语法错误和表达规范性 |

### 场景二：高后果区风险管控方案评分

| 评分项 | 权重 | 最大分值 | 描述 |
|--------|------|----------|------|
| 图像识别 | 40% | 40分 | 图像内容识别和分析 |
| 上下文逻辑 | 45% | 45分 | 文档逻辑一致性检查 |
| 处理效率 | 15% | 15分 | 处理速度和效率 |

## 🔧 配置说明

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

# 输出配置
output:
  reports_dir: "output/rag_scoring_reports"
  enable_html_reports: true
  enable_json_reports: true
```

### 环境变量

```bash
# VLLM服务配置
export VLLM_HOST=localhost
export VLLM_PORT=8000
export VLLM_MODEL_NAME=qwen2.5-vl-3b

# 系统配置
export RAG_DEBUG=false
export RAG_LOG_LEVEL=INFO
export RAG_MAX_WORKERS=4
```

## 📈 性能优化

### 系统性能要求

- **评分时间**: ≤ 120秒/份文档
- **并发处理**: 支持多文档并行处理
- **内存使用**: 优化大文档处理的内存占用
- **准确率**: 评分准确率 ≥ 85%

### 优化策略

1. **文档预处理优化**
   - 智能分块策略
   - 并行OCR处理
   - 缓存机制

2. **评分引擎优化**  
   - 评分标准配置化
   - 批量推理支持
   - 结果缓存

3. **知识库优化**
   - 向量索引优化
   - 检索结果排序
   - 增量更新支持

## 🧪 测试指南

### 单元测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定模块测试
python -m pytest tests/test_core.py -v

# 运行测试并生成覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html
```

### 集成测试

```bash
# 测试系统完整流程
./ragcli test

# 测试单个文档评分
./ragcli score data/raw/场景1\(1\).pdf --verbose

# 测试知识库功能
./ragcli kb add data/raw/场景1\(1\).pdf
./ragcli kb query "管道巡检"
```

### 性能测试

```bash
# 批量测试性能
time ./ragcli batch data/raw/

# 内存使用监控
python -m memory_profiler rag_scoring_system.py score large_document.pdf
```

## 🚨 故障排除

### 常见问题

#### 1. VLLM连接失败

```bash
# 检查VLLM服务状态
curl http://localhost:8000/health

# 检查配置
./ragcli test

# 查看详细错误
./ragcli score document.pdf --verbose
```

#### 2. 知识库初始化失败

```bash
# 清理并重建知识库
./ragcli kb clear
rm -rf output/rag_knowledge_base

# 重新初始化
./ragcli kb add data/raw/场景1\(1\).pdf
```

#### 3. 文档解析错误

```bash
# 检查文件格式支持
./ragcli status

# 查看详细错误信息
./ragcli score problematic_document.pdf --verbose
```

### 日志分析

```bash
# 查看系统日志
tail -f logs/rag_scoring_system.log

# 按日期过滤日志
grep "2025-01-" logs/rag_scoring_system.log
```

## 🔄 从旧版本迁移

### 自动迁移

```bash
# 运行迁移脚本
python migrate_to_new_architecture.py

# 查看迁移报告
cat MIGRATION_REPORT.md
```

### 手动迁移步骤

1. **备份现有数据**
   ```bash
   cp -r output/ output_backup/
   cp -r config/ config_backup/
   ```

2. **更新配置文件**
   ```bash
   # 创建新配置文件
   cp config/rag_config.yaml config/local_config.yaml
   # 手动迁移旧配置
   ```

3. **迁移知识库数据**
   ```bash
   # 重新索引文档
   ./ragcli kb clear
   ./ragcli kb add data/raw/*.pdf
   ```

4. **验证迁移结果**
   ```bash
   ./ragcli test
   ./ragcli score data/raw/场景1\(1\).pdf
   ```

## 🤝 贡献指南

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 安装pre-commit钩子
pre-commit install

# 运行代码质量检查
black src/
flake8 src/
mypy src/
```

### 代码规范

- **代码风格**: 使用Black格式化
- **类型注解**: 使用MyPy静态类型检查
- **文档字符串**: 使用Google风格文档字符串
- **测试**: 保持90%以上测试覆盖率

### 提交规范

```bash
# 提交信息格式
git commit -m "feat: 添加新功能描述"
git commit -m "fix: 修复问题描述"
git commit -m "docs: 更新文档描述"
```

## 📄 许可证

本项目采用 [MIT许可证](LICENSE)

## 📞 技术支持

- **Issues**: 通过GitHub Issues提交问题
- **Email**: 技术支持邮箱
- **文档**: 查看在线文档

## 🏆 版本历史

### v2.0.0 (重构版)
- ✅ 全新模块化架构
- ✅ 统一配置管理系统  
- ✅ 完善的CLI工具
- ✅ 标准化接口设计
- ✅ 增强的错误处理

### v1.0.0 (原始版)
- ✅ 基础评分功能
- ✅ RAG知识库集成
- ✅ VLLM推理支持
- ✅ HTML报告生成

---

## 📋 快速命令参考

```bash
# 常用命令
./ragcli test                                    # 测试系统
./ragcli score document.pdf                     # 评分文档
./ragcli batch documents/                       # 批量评分
./ragcli kb add document.pdf                    # 添加到知识库
./ragcli kb query "查询内容"                     # 查询知识库
./ragcli status                                 # 系统状态

# 配置相关
export VLLM_HOST=localhost                      # 设置VLLM主机
export VLLM_PORT=8000                          # 设置VLLM端口
./ragcli --config custom_config.yaml test      # 使用自定义配置

# 调试相关
./ragcli --verbose score document.pdf          # 详细输出
./ragcli score document.pdf --format json      # JSON格式输出
tail -f logs/rag_scoring_system.log            # 查看日志
```

**🎉 恭喜！您已成功了解RAG智能评分系统重构版的使用方法！**