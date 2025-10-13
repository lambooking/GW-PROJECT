# 部署检查清单

> 使用本清单确保系统正确部署和配置

## 📋 部署前准备

### 系统要求

- [ ] Python 3.9+ 已安装
- [ ] 8GB+ RAM 可用（推荐 16GB+）
- [ ] 5GB+ 磁盘空间可用
- [ ] 网络连接正常（用于下载模型）

### 权限检查

- [ ] 对项目目录有读写权限
- [ ] 可以安装 Python 包
- [ ] 可以安装系统包（antiword）或已有 sudo 权限

## 🔧 安装步骤

### 1. Python 依赖

```bash
# 进入项目目录
cd /path/to/GW-PROJECT/GW-PROJECT

# 安装依赖
pip install -r requirements.txt
```

验证：
```bash
pip list | grep -E "(modelscope|sentence-transformers|chromadb)"
```

- [ ] modelscope 已安装
- [ ] sentence-transformers 已安装
- [ ] chromadb 已安装

### 2. antiword 工具

```bash
# Ubuntu/Debian
sudo apt-get install -y antiword

# CentOS/RHEL
sudo yum install -y antiword
```

验证：
```bash
which antiword
antiword -v
```

- [ ] antiword 命令可用
- [ ] 显示版本信息

### 3. Embedding 模型

```bash
# 运行下载脚本
python scripts/download_embedding_model.py
```

验证：
```bash
ls -lh /home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base/
```

- [ ] 模型目录存在
- [ ] 包含 config.json
- [ ] 包含 pytorch_model.bin
- [ ] 总大小约 400MB

### 4. VLLM 服务

确认 VLLM 服务正在运行：

```bash
curl http://localhost:8000/v1/models
```

- [ ] VLLM 服务可访问
- [ ] 返回模型列表

## 🧪 功能验证

### 验证 1: 运行自动验证脚本

```bash
python scripts/verify_fixes.py
```

预期输出：
```
✅ 通过: 6
⚠️  警告: 0
❌ 失败: 0
🎉 所有检查通过！系统已正确配置
```

- [ ] 所有检查通过（0 失败）
- [ ] 无严重警告

### 验证 2: 测试模型加载

```bash
python3 << 'EOF'
from src.inference.rag_knowledge_base import EmbeddingModel
model = EmbeddingModel()
embeddings = model.encode(["测试"])
print(f"✅ 向量维度: {len(embeddings[0])}")
assert len(embeddings[0]) == 768, "向量维度错误"
print("✅ 模型测试通过")
EOF
```

- [ ] 模型加载成功
- [ ] 向量维度为 768
- [ ] 无 "随机向量" 警告

### 验证 3: 测试 DOC 解析

创建测试文件 `test_doc.py`:
```bash
cat > test_doc.py << 'EOF'
from src.data.parsers.docx_parser import DocxDocumentParser, ANTIWORD_AVAILABLE
from pathlib import Path

parser = DocxDocumentParser()
print(f"✅ 支持 .doc: {parser.supports_format(Path('test.doc'))}")
print(f"✅ 支持 .docx: {parser.supports_format(Path('test.docx'))}")
print(f"✅ antiword 可用: {ANTIWORD_AVAILABLE}")
EOF

python test_doc.py
rm test_doc.py
```

- [ ] 支持 .doc 格式
- [ ] 支持 .docx 格式
- [ ] antiword 可用（如果安装了）

### 验证 4: 重建知识库

```bash
# 清空旧数据
rm -rf output/rag_knowledge_base/chromadb/

# 重新索引
python quick_reindex.py
```

预期输出应包含：
```
INFO - ✅ 成功从本地加载模型
INFO - Successfully indexed: 'XXX' with XXX chunks
```

- [ ] 模型从本地加载（不是下载）
- [ ] 至少索引了 1 个文档
- [ ] total_chunks > 0
- [ ] 无 "随机向量" 警告

### 验证 5: 运行评分测试

```bash
# 使用测试文档
python run_complete_rag_scoring.py score /path/to/test/document.pdf
```

关键检查点：

**模型加载**:
- [ ] 看到 "✅ 成功从本地加载模型"
- [ ] 看到 "向量维度: 768"
- [ ] 没有 "使用随机向量" 警告

**内容检索**:
- [ ] 看到 "检索到上下文长度: XXX 字符"
- [ ] 上下文长度 > 0

**评分结果**:
- [ ] 总分 > 0（不是 0/100）
- [ ] 各评分项有详细理由
- [ ] 不是所有项都显示 "未找到相关内容"
- [ ] 生成了 HTML 报告

## 🎯 性能基准

运行以下命令测试性能：

```bash
time python run_complete_rag_scoring.py score test.pdf
```

记录结果：

| 指标 | 预期值 | 实际值 | 状态 |
|------|--------|--------|------|
| 文档解析 | < 60秒 | _____ | [ ] |
| 向量生成 | < 5秒 | _____ | [ ] |
| 内容检索 | < 10秒 | _____ | [ ] |
| 评分推理 | < 60秒 | _____ | [ ] |
| 总耗时 | < 120秒 | _____ | [ ] |

## 🐛 常见问题排查

### 问题 1: 评分仍为 0

**检查步骤**:
1. [ ] 运行 `python scripts/verify_fixes.py` 查看具体问题
2. [ ] 确认知识库不为空: `ls -lh output/rag_knowledge_base/chromadb/`
3. [ ] 重建知识库: `rm -rf output/rag_knowledge_base/chromadb/ && python quick_reindex.py`
4. [ ] 查看日志: `tail -100 logs/rag_scoring_*.log`

### 问题 2: 模型加载失败

**检查步骤**:
1. [ ] 确认模型目录存在: `ls /home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base/`
2. [ ] 重新下载: `python scripts/download_embedding_model.py`
3. [ ] 检查网络: `ping modelscope.cn`
4. [ ] 使用镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple modelscope`

### 问题 3: antiword 不可用

**检查步骤**:
1. [ ] 确认安装: `which antiword`
2. [ ] 重新安装: `sudo apt-get install antiword` 或 `sudo yum install antiword`
3. [ ] 临时方案: 将 .doc 文件转换为 .docx

### 问题 4: 内存不足

**检查步骤**:
1. [ ] 查看内存: `free -h`
2. [ ] 关闭其他服务释放内存
3. [ ] 考虑使用更小的模型（需修改配置）

## 📝 部署记录

### 部署信息

- **部署日期**: _______________
- **部署人员**: _______________
- **服务器地址**: _______________
- **Python 版本**: _______________
- **操作系统**: _______________

### 验证结果

- **自动验证**: [ ] 通过 [ ] 失败
- **模型加载**: [ ] 正常 [ ] 异常
- **DOC 解析**: [ ] 正常 [ ] 异常
- **评分测试**: [ ] 正常 [ ] 异常

### 性能数据

- **模型加载时间**: _____秒
- **单文档评分**: _____秒
- **内存使用**: _____GB
- **磁盘使用**: _____GB

### 备注

```
记录部署过程中的任何问题或特殊情况:

_______________________________________________
_______________________________________________
_______________________________________________
```

## ✅ 最终确认

在生产环境使用前，确认以下所有项：

- [ ] 所有依赖已正确安装
- [ ] Embedding 模型已下载并可用
- [ ] antiword 工具已安装（如需 .doc 支持）
- [ ] 知识库已建立且包含文档
- [ ] 评分测试通过（分数 > 0）
- [ ] 性能满足要求
- [ ] 日志输出正常，无错误警告
- [ ] HTML 报告可以正常生成
- [ ] 团队成员已培训使用方法

## 📞 支持资源

- **快速开始**: [QUICKSTART_AFTER_FIX.md](./QUICKSTART_AFTER_FIX.md)
- **配置指南**: [docs/EMBEDDING_MODEL_SETUP.md](./docs/EMBEDDING_MODEL_SETUP.md)
- **测试指南**: [docs/TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)
- **修复总结**: [docs/FIX_SUMMARY.md](./docs/FIX_SUMMARY.md)
- **验证脚本**: `scripts/verify_fixes.py`

---

**部署完成日期**: _______________  
**部署负责人签字**: _______________


