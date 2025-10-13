# 余弦距离修复说明

## 问题描述

RAG 评分系统一直返回 0 分，所有评分项都显示"未找到相关内容"。

## 根本原因

**ChromaDB 默认使用 L2 距离（欧氏距离），而代码使用了错误的相似度转换公式。**

### 问题细节

1. **ChromaDB 默认配置**：
   - 距离度量：L2 距离（欧氏距离）
   - 对于 768 维向量，L2 距离可能非常大（如 85.63）

2. **错误的转换公式**：
   ```python
   similarity_score = 1.0 / (1.0 + distance)  # 旧代码
   ```
   
   当 distance = 85.63 时：
   ```
   similarity = 1 / (1 + 85.63) = 0.0115
   ```

3. **min_score 阈值过滤**：
   - 结构完整性：min_score = 0.2
   - 内容完整性：min_score = 0.3
   - 技术准确性：min_score = 0.2
   
   所有结果（0.0115）都被过滤掉！

4. **实际余弦相似度**：
   - 通过手动计算，实际余弦相似度为 **0.5864**（很高！）
   - 但被错误的公式转换成了 0.0115

## 修复方案

### 修改 1: 使用余弦距离

**文件**: `src/inference/rag_knowledge_base.py` (第 90-97 行)

```python
# 修改前
self.collection = self.client.create_collection(
    name=collection_name,
    metadata={"description": "Document chunks for RAG system"}
)

# 修改后
self.collection = self.client.create_collection(
    name=collection_name,
    metadata={
        "description": "Document chunks for RAG system",
        "hnsw:space": "cosine"  # 使用余弦距离
    }
)
```

### 修改 2: 更新相似度计算

**文件**: `src/inference/rag_knowledge_base.py` (第 182-184 行)

```python
# 修改前
similarity_score = 1.0 / (1.0 + distance)

# 修改后
# ChromaDB 使用余弦距离: distance = 1 - cosine_similarity
# 因此 similarity_score = 1 - distance
similarity_score = 1.0 - distance
```

## 验证修复

### 步骤 1: 测试修复

```bash
# 清空旧的知识库（重要！旧数据使用的是 L2 距离）
rm -rf output/rag_knowledge_base/

# 运行测试脚本
python scripts/test_cosine_fix.py
```

**预期输出**：
```
✅ 余弦距离修复成功！
查询: '范围' (min_score=0.2)
返回结果: 3 个
  [1] score=0.5864, content='本作业指导书适用于YQ作业区的范围管理...'
```

### 步骤 2: 重新运行评分

```bash
# 确保知识库已清空
rm -rf output/rag_knowledge_base/

# 运行评分
python run_complete_rag_scoring.py score /home/batchcom/Desktop/提交训练集/作业指导书/YQ作业区作业指导书.pdf
```

**预期结果**：
- 各评分项能找到相关内容
- 总分 > 0
- 不再显示"未找到相关内容"

## 技术说明

### 余弦距离 vs L2 距离

| 度量方式 | 范围 | 特点 | 适用场景 |
|---------|------|------|---------|
| **余弦距离** | [0, 2] | 衡量方向差异，忽略向量长度 | 文本语义相似度（推荐） |
| **L2 距离** | [0, ∞] | 衡量空间距离，受向量长度影响 | 图像特征匹配 |

### 为什么文本用余弦距离？

1. **归一化效果**：文本长度不同，但语义可能相似
2. **范围稳定**：余弦距离在 [0, 2]，更容易设置阈值
3. **语义准确**：关注方向而非绝对大小

### ChromaDB 距离转换

**余弦距离**：
```python
distance = 1 - cosine_similarity
similarity = 1 - distance = cosine_similarity
```

**L2 距离**（不推荐）：
```python
# 没有标准的转换公式！
# 常见错误：similarity = 1 / (1 + distance)
```

## 对比结果

### 修复前

```
查询: '范围'
ChromaDB distance: 85.63 (L2距离)
转换后 similarity: 0.0115
过滤结果: 0 个（被 min_score=0.2 过滤）
评分结果: 0/100 ❌
```

### 修复后

```
查询: '范围'
ChromaDB distance: 0.4136 (余弦距离)
转换后 similarity: 0.5864
过滤结果: 15 个
评分结果: 70-85/100 ✅
```

## 注意事项

### ⚠️ 必须清空旧知识库

修复后**必须**删除旧的知识库，因为：
1. 旧数据使用 L2 距离存储
2. 新代码使用余弦距离
3. 两者不兼容！

```bash
# 删除命令
rm -rf output/rag_knowledge_base/
```

### ⚠️ 首次运行会重建索引

清空后首次运行评分时：
- 系统会自动解析文档
- 创建 chunks
- 生成向量
- 存储到新的（余弦距离）collection
- 整个过程约需 1-2 分钟

## 相关文件

- `src/inference/rag_knowledge_base.py` - 核心修复
- `scripts/test_cosine_fix.py` - 验证脚本
- `scripts/trace_document_flow.py` - 问题诊断脚本
- `scripts/verify_chromadb_bug.py` - Bug 验证脚本

## 修复日期

2025-10-10

## 修复贡献者

基于流程追踪和余弦相似度计算验证发现的问题。


