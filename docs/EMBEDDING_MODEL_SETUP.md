# Embedding 模型配置指南

## 概述

本项目已更新为使用魔塔社区（ModelScope）的中文 Embedding 模型，以获得更好的中文文本理解能力，并支持离线环境使用。

## 模型信息

- **模型名称**: `iic/nlp_gte_sentence-embedding_chinese-base`
- **向量维度**: 768
- **适用场景**: 中文文本语义检索
- **本地路径**: `/home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base`

## 安装步骤

### 1. 安装依赖包

```bash
# 安装核心依赖
pip install sentence-transformers>=2.2.0
pip install modelscope>=1.9.0
pip install chromadb>=0.4.0

# 或者使用 requirements.txt
pip install -r requirements.txt
```

### 2. 下载模型

#### 方法一：使用下载脚本（推荐）

```bash
# 使用默认配置下载
python scripts/download_embedding_model.py

# 或指定自定义路径
python scripts/download_embedding_model.py \
  --model-id iic/nlp_gte_sentence-embedding_chinese-base \
  --local-path /home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base
```

脚本会：
- 自动检查依赖
- 从魔塔社区下载模型
- 验证模型可用性
- 显示下载进度

#### 方法二：手动下载

如果服务器完全无网络，可以在有网络的机器上下载后传输：

```python
# 在有网络的机器上执行
from modelscope import snapshot_download

model_dir = snapshot_download(
    'iic/nlp_gte_sentence-embedding_chinese-base',
    cache_dir='/tmp/models'
)
print(f"模型已下载到: {model_dir}")
```

然后将整个目录打包传输到服务器：

```bash
# 打包
tar -czf embedding_model.tar.gz /tmp/models/nlp_gte_sentence-embedding_chinese-base

# 在目标服务器上解压
tar -xzf embedding_model.tar.gz -C /home/dataset-assist-0/models/
```

### 3. 验证模型

```bash
# 运行验证脚本
python scripts/download_embedding_model.py
```

如果看到以下输出，说明模型配置成功：

```
✅ 模型加载成功
📊 向量维度: 768
📝 测试编码: 3 个文本
🎉 模型下载并验证成功！
```

## DOC 文件支持

### 安装 antiword

系统现在支持老版本的 `.doc` 文件（二进制格式）。需要安装 `antiword` 工具：

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install antiword
```

#### CentOS/RHEL

```bash
sudo yum install antiword
```

#### 验证安装

```bash
antiword -v
```

如果显示版本号，说明安装成功。

## 使用方法

### RAG 评分系统

模型配置完成后，直接运行评分即可：

```bash
# 评分 PDF 文件
python run_complete_rag_scoring.py score /path/to/document.pdf

# 评分 DOCX 文件
python run_complete_rag_scoring.py score /path/to/document.docx

# 评分 DOC 文件（需要 antiword）
python run_complete_rag_scoring.py score /path/to/document.doc
```

系统会：
1. 自动从本地路径加载模型
2. 如果本地不存在，尝试从魔塔社区下载
3. 生成高质量的中文文本向量
4. 执行语义检索和智能评分

### 重新索引知识库

如果更换了 Embedding 模型，需要重新索引知识库：

```bash
# 清空旧的向量数据库
rm -rf output/rag_knowledge_base/chromadb/

# 重新索引
python quick_reindex.py
```

## 常见问题

### Q1: 模型下载失败

**问题**: 提示 "从魔塔社区下载模型失败"

**解决**:
1. 检查网络连接
2. 确认 modelscope 已安装: `pip install modelscope`
3. 尝试使用代理: `export http_proxy=...`
4. 使用手动下载方法

### Q2: 向量维度不匹配

**问题**: "Embedding dimension mismatch"

**解决**:
1. 清空旧的向量数据库: `rm -rf output/rag_knowledge_base/chromadb/`
2. 重新索引: `python quick_reindex.py`

### Q3: DOC 文件解析失败

**问题**: ".doc 文件需要 antiword 工具支持"

**解决**:
1. 安装 antiword: `sudo apt-get install antiword`
2. 或将 .doc 文件转换为 .docx 格式

### Q4: 评分仍然为 0

**问题**: 修复后评分仍为 0

**检查清单**:
1. ✅ 模型是否正确加载？查看日志中是否有 "✅ 成功从本地加载模型"
2. ✅ 知识库是否有内容？运行 `python quick_reindex.py` 先索引文档
3. ✅ 向量检索是否有结果？查看日志中 "检索到上下文长度"

## 性能优化

### 批量处理

对于大批量文档，建议：

```bash
# 先批量索引到知识库
python quick_reindex.py

# 再批量评分
python run_complete_rag_scoring.py batch /path/to/documents/
```

### 内存使用

中文 GTE 模型约占用 1-2GB 内存。如果内存有限，可以考虑使用更小的模型：

```python
# 在 rag_knowledge_base.py 中修改
model_name = "damo/nlp_corom_sentence-embedding_chinese-small"
local_model_path = "/home/dataset-assist-0/models/nlp_corom_sentence-embedding_chinese-small"
```

## 技术细节

### 模型加载顺序

1. 检查本地路径 `/home/dataset-assist-0/models/` 是否存在模型
2. 如果不存在，从魔塔社区下载
3. 下载后保存到本地，供后续使用

### 文件格式支持

| 格式 | 解析器 | 特性 |
|------|--------|------|
| `.pdf` | PDFDocumentParser | 支持 OCR、表格、图片提取 |
| `.docx` | DocxDocumentParser | 支持文本、表格、图片提取 |
| `.doc` | DocxDocumentParser + antiword | 仅文本提取，不支持表格和图片 |

### 向量维度说明

- 原模型 (all-MiniLM-L6-v2): 384 维，英文优化
- 新模型 (GTE-chinese-base): 768 维，中文优化
- 维度更高意味着更细粒度的语义表示

## 相关文件

- `src/inference/rag_knowledge_base.py` - Embedding 模型实现
- `src/data/parsers/docx_parser.py` - DOC/DOCX 文件解析器
- `scripts/download_embedding_model.py` - 模型下载工具
- `requirements.txt` - 项目依赖

## 更新日志

- 2025-10-10: 添加魔塔社区模型支持
- 2025-10-10: 添加 .doc 文件解析（antiword）
- 2025-10-10: 移除随机向量 fallback，强制使用真实模型


