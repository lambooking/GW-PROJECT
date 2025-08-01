# 生产运维管理AI审核系统

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 项目简介

生产运维管理AI审核系统是一个基于人工智能技术的智能文档审核平台，专门用于生产运维管理领域的文档质量评估和合规性检查。

### 主要功能

- 📄 **作业指导书审核**: 智能评估作业指导书的结构完整性、内容完整性、语法错误等
- 🏗️ **风险管控方案审核**: 多模态审核高后果区风险管控方案，包括图像识别和文本分析
- 📊 **智能报告生成**: 自动生成详细的审核报告，支持HTML和Excel格式
- 🚀 **批量处理**: 支持批量文档审核，提高工作效率
- 🔍 **多模态分析**: 结合文本和图像信息进行综合评估

### 系统特性

- ✅ **高准确率**: 审核准确率≥85%，F1值≥85%
- ⚡ **高效处理**: 单份文档审核时间≤120秒
- 🔄 **批量支持**: 支持批量文档处理
- 📱 **友好界面**: 提供直观的Web API接口
- 🛡️ **信创兼容**: 支持信创环境部署

## 快速开始

### 环境要求

- Python 3.9+
- 8GB+ RAM
- 支持CUDA的GPU（可选，用于加速）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd GW-PROJECT
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置系统**
```bash
# 复制配置文件
cp config/config.yaml.example config/config.yaml

# 根据需要修改配置
vim config/config.yaml
```

4. **启动服务**
```bash
# 启动API服务
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# 或使用脚本启动
python scripts/start_server.py
```

### 使用示例

#### API调用示例

```python
import requests

# 审核作业指导书
with open('document.docx', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/audit/instruction-book',
        files={'file': f}
    )
    result = response.json()
    print(f"审核得分: {result['results']['overall_score']:.2f}")
```

#### 命令行使用

```bash
# 单文档审核
python scripts/audit_document.py document.docx --type instruction_book

# 批量审核
python scripts/batch_audit.py ./documents/ --output ./results/
```

## 项目结构

```
GW-PROJECT/
├── config/                 # 配置文件
│   ├── config.yaml         # 主配置文件
│   └── model_config.py     # 模型配置
├── src/                    # 源代码
│   ├── common/             # 通用工具
│   ├── data_processing/    # 数据处理
│   ├── models/             # AI模型
│   ├── inference/          # 推理引擎
│   └── api/                # API接口
├── scripts/                # 实用脚本
├── data/                   # 数据目录
├── output/                 # 输出目录
│   ├── reports/            # 审核报告
│   └── logs/               # 日志文件
└── deployment/             # 部署配置
```

## API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/audit/instruction-book` | POST | 审核作业指导书 |
| `/audit/risk-management` | POST | 审核风险管控方案 |
| `/audit/batch` | POST | 批量文档审核 |
| `/health` | GET | 健康检查 |

## 配置说明

### 系统配置 (config/config.yaml)

```yaml
# 系统配置
system:
  debug: false
  log_level: "INFO"
  max_workers: 4
  gpu_enabled: true

# 模型配置
models:
  text_audit:
    model_name: "chinese-roberta-wwm-ext"
    max_length: 512
    batch_size: 16
  
  multimodal_audit:
    vision_model: "chinese-clip-vit-base-patch16"
    text_model: "chinese-roberta-wwm-ext"
    fusion_dim: 768

# 审核规则配置
audit_rules:
  instruction_book:
    structure_completeness:
      required_sections: ["目录", "职责", "作业内容", "相关文件", "记录文件"]
      scoring_weight: 0.2
    content_completeness:
      scoring_weight: 0.4
    # ... 其他配置
```

## 开发指南

### 添加新的审核规则

1. 在 `src/models/` 中实现审核模型
2. 在 `config/config.yaml` 中添加规则配置
3. 在 `src/inference/audit_engine.py` 中注册新规则

### 扩展支持的文档格式

1. 在 `src/data_processing/document_parser.py` 中添加解析器
2. 更新 `src/common/constants.py` 中的支持格式列表

## 部署指南

### Docker部署

```bash
# 构建镜像
docker build -t ai-audit-system .

# 运行容器
docker run -p 8000:8000 ai-audit-system
```

### 使用docker-compose

```bash
docker-compose up -d
```

## 性能优化

### GPU加速

确保安装了CUDA和相应的PyTorch版本：

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 批量处理优化

- 调整 `max_workers` 参数控制并发数
- 使用SSD存储提高I/O性能
- 增加内存以支持更大批量

## 监控和日志

### 日志配置

日志文件位置: `output/logs/`

### 性能监控

- 处理时间统计
- 内存使用监控
- GPU利用率监控

## 常见问题

### Q: 如何处理大文件？

A: 系统默认支持最大50MB的文件。如需处理更大文件，请修改配置文件中的 `max_file_size` 参数。

### Q: 如何提高审核准确率？

A: 可以通过以下方式提高准确率：
- 使用更大的预训练模型
- 增加训练数据
- 调整审核规则权重

### Q: 支持哪些文档格式？

A: 目前支持：
- Microsoft Word (.docx, .doc)
- PDF (.pdf)

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献指南

欢迎贡献代码！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

## 联系我们

- 项目主页: [dengxianchi]
- 问题反馈: [Issues]
- 邮箱: [Contact Email]

---

**注意**: 这是一个AI竞赛项目，仅供学习和研究使用。