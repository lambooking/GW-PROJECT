# RAG 评分系统测试指南

本指南帮助您验证修复后的 RAG 评分系统是否正常工作。

## 测试环境准备

### 1. 安装依赖

```bash
cd /path/to/GW-PROJECT/GW-PROJECT
pip install -r requirements.txt
```

确保安装了以下关键包：
- `sentence-transformers>=2.2.0`
- `modelscope>=1.9.0`
- `chromadb>=0.4.0`
- `python-docx>=0.8.11`

### 2. 安装 antiword（用于 .doc 文件支持）

```bash
# Ubuntu/Debian
sudo apt-get install antiword

# CentOS/RHEL
sudo yum install antiword

# 验证安装
antiword -v
```

### 3. 下载 Embedding 模型

```bash
# 运行模型下载脚本
python scripts/download_embedding_model.py
```

等待下载完成，应该看到：
```
✅ 模型加载成功
📊 向量维度: 768
🎉 模型下载并验证成功！
```

## 测试步骤

### 测试 1: 验证模型加载

```bash
# 启动 Python 交互式环境
python3
```

```python
# 测试模型加载
from src.inference.rag_knowledge_base import EmbeddingModel

# 创建模型实例
model = EmbeddingModel()

# 测试编码
texts = ["这是一个测试句子", "RAG评分系统", "作业指导书"]
embeddings = model.encode(texts)

print(f"✅ 模型加载成功")
print(f"📊 向量维度: {len(embeddings[0])}")
print(f"📝 编码文本数: {len(embeddings)}")
```

**预期结果**:
- 不应该看到 "使用随机向量" 的警告
- 向量维度应该是 768
- 编码成功完成

### 测试 2: 验证 .doc 文件解析

创建一个测试脚本 `test_doc_parser.py`:

```python
#!/usr/bin/env python3
from pathlib import Path
from src.data.parsers.docx_parser import DocxDocumentParser

# 测试 .doc 文件解析
def test_doc_parsing():
    parser = DocxDocumentParser()
    
    # 替换为您的实际 .doc 文件路径
    doc_file = Path("/path/to/your/test.doc")
    
    if not doc_file.exists():
        print(f"⚠️  测试文件不存在: {doc_file}")
        print("   请提供一个 .doc 文件进行测试")
        return
    
    try:
        print(f"📄 解析文件: {doc_file}")
        document = parser.parse(doc_file)
        
        print(f"✅ 解析成功!")
        print(f"  文件名: {document.document_info.file_name}")
        print(f"  页数: {document.document_info.total_pages}")
        print(f"  文本段落数: {len(document.text_content)}")
        print(f"  前 100 字符: {document.raw_content[:100]}...")
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")

if __name__ == "__main__":
    test_doc_parsing()
```

运行测试：

```bash
python test_doc_parser.py
```

**预期结果**:
- 如果 antiword 未安装，会看到明确的错误提示
- 如果已安装，应该成功提取文本内容

### 测试 3: 重建知识库

```bash
# 清空旧的向量数据库（使用旧模型的数据）
rm -rf output/rag_knowledge_base/chromadb/

# 重新索引文档
python quick_reindex.py
```

**预期输出**:
```
INFO - ✅ 成功从本地加载模型: /home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base
INFO - Successfully indexed: '场景1(1).pdf' with XXX chunks
INFO - 📊 Final stats: {'total_documents': 1, 'total_chunks': XXX, ...}
```

**关键检查点**:
- ❌ 不应该看到 "使用随机向量" 的警告
- ✅ 应该看到 "成功从本地加载模型"
- ✅ `total_chunks` 应该大于 0

### 测试 4: 运行完整评分

```bash
# 使用您之前测试失败的文件
python run_complete_rag_scoring.py score /home/batchcom/Desktop/提交训练集/作业指导书/YQ作业区作业指导书.pdf
```

**关键观察点**:

1. **模型加载**:
```
✅ 成功从本地加载模型: /home/dataset-assist-0/models/...
```

2. **向量生成**:
```
INFO - Generated XXX embeddings.
INFO - First embedding shape: (768,), first 5 values: [0.123, -0.456, ...]
```
注意：不应该再看到 "使用随机向量" 的警告！

3. **内容检索**:
```
INFO - 检索到上下文长度: XXX 字符，包含 X 个片段
```
长度应该 > 0，不应该是空的！

4. **评分结果**:
```
🎯 总体评分:
   - 总分: XX/100  (应该 > 0)
   - 得分率: XX.X%  (应该 > 0.0%)
   - 等级: 及格/良好/优秀 (不应该是 "不及格")
```

**如果还是 0 分，检查**:
- 知识库是否为空？运行 `python quick_reindex.py`
- 文档是否正确添加到知识库？查看 `output/rag_knowledge_base/document_registry.json`
- 向量检索是否返回结果？查看日志中 "ChromaDB raw query results"

### 测试 5: 测试不同文件格式

```bash
# 测试 PDF
python run_complete_rag_scoring.py score document.pdf

# 测试 DOCX
python run_complete_rag_scoring.py score document.docx

# 测试 DOC
python run_complete_rag_scoring.py score document.doc
```

## 常见问题诊断

### 问题 1: 评分仍然为 0

**症状**: 
```
INFO - 内容完整性: 未找到相关内容
总分: 0/100
```

**诊断步骤**:

1. 检查知识库状态:
```python
from src.inference.rag_knowledge_base import RAGKnowledgeBase
kb = RAGKnowledgeBase()
stats = kb.get_stats()
print(stats)
```

应该看到:
```python
{
    'total_documents': 1,  # 应该 > 0
    'total_chunks': 150,   # 应该 > 0
    ...
}
```

2. 测试搜索功能:
```python
results = kb.search("范围", top_k=5)
print(f"搜索结果: {len(results)} 个")
for i, r in enumerate(results[:3]):
    print(f"  [{i+1}] score={r['score']:.4f}, content={r['content'][:50]}...")
```

应该返回相关结果，score > 0.3

3. 如果知识库为空或搜索无结果，重新索引:
```bash
rm -rf output/rag_knowledge_base/chromadb/
python quick_reindex.py
```

### 问题 2: 模型加载失败

**症状**:
```
ERROR - ❌ Embedding模型加载失败
```

**解决**:
```bash
# 重新下载模型
python scripts/download_embedding_model.py

# 检查路径是否正确
ls -lh /home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base/
```

### 问题 3: .doc 文件解析失败

**症状**:
```
ERROR - .doc 文件需要 antiword 工具支持
```

**解决**:
```bash
# 安装 antiword
sudo apt-get install antiword  # Ubuntu/Debian
sudo yum install antiword      # CentOS/RHEL

# 验证安装
which antiword
antiword -v
```

### 问题 4: 向量维度不匹配

**症状**:
```
ERROR - Embedding dimension mismatch: expected 384, got 768
```

**解决**:
```bash
# 旧模型的向量数据库不兼容，需要清空重建
rm -rf output/rag_knowledge_base/chromadb/
python quick_reindex.py
```

## 性能测试

### 测试向量生成速度

```python
from src.inference.rag_knowledge_base import EmbeddingModel
import time

model = EmbeddingModel()

# 测试不同批量大小
for batch_size in [1, 10, 50, 100]:
    texts = [f"测试文本 {i}" for i in range(batch_size)]
    
    start = time.time()
    embeddings = model.encode(texts)
    elapsed = time.time() - start
    
    print(f"批量大小: {batch_size:3d}, 耗时: {elapsed:.3f}秒, "
          f"速度: {batch_size/elapsed:.1f} 文本/秒")
```

**参考性能** (CPU):
- 1 文本: ~0.05秒
- 10 文本: ~0.2秒
- 50 文本: ~0.8秒
- 100 文本: ~1.5秒

### 测试评分速度

```bash
# 记录评分时间
time python run_complete_rag_scoring.py score document.pdf
```

**参考时间** (CPU):
- 小文档 (10页): ~30秒
- 中等文档 (50页): ~90秒
- 大文档 (100页): ~180秒

## 验收标准

所有测试通过的标志：

- ✅ Embedding 模型成功加载（768维）
- ✅ 不再出现 "使用随机向量" 警告
- ✅ .doc 文件可以成功解析
- ✅ 知识库成功建立（total_chunks > 0）
- ✅ 向量检索返回相关结果
- ✅ 评分结果 > 0 分
- ✅ 各评分项都有详细的评分理由

## 获取帮助

如果测试遇到问题：

1. 查看日志文件: `logs/rag_scoring_*.log`
2. 检查配置: `output/rag_knowledge_base/document_registry.json`
3. 参考文档: `docs/EMBEDDING_MODEL_SETUP.md`


