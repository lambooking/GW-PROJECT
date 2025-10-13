# 快速开始指南 - 修复后版本

> 本指南帮助您快速配置和使用修复后的 RAG 评分系统

## 🚀 5分钟快速部署

### 1. 安装依赖包 (1分钟)

```bash
cd /path/to/GW-PROJECT/GW-PROJECT

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 antiword（用于 .doc 文件支持）
# Ubuntu/Debian
sudo apt-get install -y antiword

# CentOS/RHEL
sudo yum install -y antiword
```

### 2. 下载 Embedding 模型 (2-3分钟)

```bash
# 运行自动下载脚本
python scripts/download_embedding_model.py
```

看到以下输出表示成功：
```
✅ 模型加载成功
📊 向量维度: 768
🎉 模型下载并验证成功！
```

### 3. 重建知识库 (1分钟)

```bash
# 清空旧数据（重要！）
rm -rf output/rag_knowledge_base/chromadb/

# 重新索引文档
python quick_reindex.py
```

看到类似输出：
```
INFO - ✅ 成功从本地加载模型
INFO - Successfully indexed: 'XXX.pdf' with XXX chunks
```

### 4. 运行评分测试 (<1分钟)

```bash
# 使用您之前测试失败的文件
python run_complete_rag_scoring.py score /home/batchcom/Desktop/提交训练集/作业指导书/YQ作业区作业指导书.pdf
```

**预期结果**：
- ✅ 总分应该 > 0（不再是 0/100）
- ✅ 各评分项都有详细理由（不再是"未找到相关内容"）
- ✅ 生成 HTML 报告

## 📋 验证检查清单

运行以下命令快速验证系统状态：

```bash
# 1. 检查依赖
pip list | grep -E "(modelscope|sentence-transformers|chromadb)"
# 应该看到三个包都已安装

# 2. 检查 antiword
which antiword
# 应该显示路径，如 /usr/bin/antiword

# 3. 检查模型
ls -lh /home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base/
# 应该看到模型文件（约 400MB）

# 4. 检查知识库
ls -lh output/rag_knowledge_base/chromadb/
# 应该看到 chromadb 数据文件
```

## 🎯 使用示例

### 评分单个文档

```bash
# PDF 文件
python run_complete_rag_scoring.py score /path/to/document.pdf

# DOCX 文件
python run_complete_rag_scoring.py score /path/to/document.docx

# DOC 文件（需要 antiword）
python run_complete_rag_scoring.py score /path/to/document.doc
```

### 批量评分

```bash
# 评分整个目录的所有 PDF
python run_complete_rag_scoring.py batch /path/to/documents/
```

### 查看评分报告

```bash
# HTML 报告位置
ls -lt output/rag_scoring_reports/html/

# 在浏览器中打开（如果有图形界面）
firefox output/rag_scoring_reports/html/rag_scoring_report_XXX.html
```

## 🔧 核心改进说明

### 改进 1: 中文 Embedding 模型

- **旧版**: 使用英文模型 all-MiniLM-L6-v2 (384维)
- **新版**: 使用中文模型 GTE-chinese-base (768维)
- **效果**: 中文语义理解能力大幅提升

### 改进 2: 支持 .doc 文件

- **旧版**: 只支持 .docx 和 .pdf
- **新版**: 支持 .doc、.docx、.pdf 三种格式
- **方案**: 使用 antiword 工具提取 .doc 文本

### 改进 3: 移除随机向量 Fallback

- **旧版**: 模型加载失败时使用随机向量（导致 0 分）
- **新版**: 强制使用真实模型，失败则明确报错
- **效果**: 不再出现"评分全 0"的问题

## 📊 性能参考

在典型的 CPU 服务器上（无 GPU）：

| 操作 | 文档大小 | 耗时 |
|------|---------|------|
| 模型下载 | 400MB | 2-5分钟 |
| 文档解析 | 50页 | 30-60秒 |
| 向量生成 | 100个文本 | 1-2秒 |
| 单文档评分 | 50页 | 90-120秒 |

## ⚠️ 常见问题快速解决

### 问题 1: 评分仍然为 0

```bash
# 解决方案：清空并重建知识库
rm -rf output/rag_knowledge_base/chromadb/
python quick_reindex.py
# 再次运行评分
python run_complete_rag_scoring.py score /path/to/document.pdf
```

### 问题 2: 模型下载失败

```bash
# 解决方案：使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple modelscope
# 重新下载
python scripts/download_embedding_model.py
```

### 问题 3: .doc 文件解析失败

```bash
# 解决方案：安装 antiword
sudo apt-get install antiword  # Ubuntu/Debian
sudo yum install antiword      # CentOS/RHEL
# 或者转换为 .docx
libreoffice --headless --convert-to docx document.doc
```

### 问题 4: 内存不足

```bash
# 查看内存使用
free -h

# 如果内存 < 4GB，关闭其他服务
# 或者修改配置使用更小的模型
```

## 📚 详细文档

如需更多信息，请参考：

- **配置指南**: `docs/EMBEDDING_MODEL_SETUP.md`
- **测试指南**: `docs/TESTING_GUIDE.md`
- **修复总结**: `docs/FIX_SUMMARY.md`
- **技术报告**: `docs/rag-tech-report.md`

## 💡 最佳实践

### 1. 首次使用

```bash
# 完整流程
pip install -r requirements.txt
python scripts/download_embedding_model.py
rm -rf output/rag_knowledge_base/chromadb/
python quick_reindex.py
python run_complete_rag_scoring.py score test.pdf
```

### 2. 日常使用

```bash
# 如果模型和知识库已配置好
python run_complete_rag_scoring.py score new_document.pdf
```

### 3. 批量处理

```bash
# 先索引所有文档到知识库
python quick_reindex.py

# 再批量评分
python run_complete_rag_scoring.py batch /path/to/documents/
```

## 🎓 下一步

1. **测试评分功能**: 使用您的实际文档测试
2. **检查报告质量**: 查看生成的 HTML 报告
3. **调优参数**: 根据需要调整评分标准（在 `rag_scoring_engine.py` 中）
4. **批量处理**: 处理更多文档建立知识库

## 📞 获取帮助

如果遇到问题：

1. 查看日志文件: `logs/rag_scoring_*.log`
2. 检查测试指南: `docs/TESTING_GUIDE.md`
3. 参考配置文档: `docs/EMBEDDING_MODEL_SETUP.md`

---

**祝您使用顺利！** 🎉


