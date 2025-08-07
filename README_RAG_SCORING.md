# RAG智能评分系统使用指南

## 概述

基于RAG（检索增强生成）技术的智能文档评分系统，通过动态检索文档内容并结合大语言模型，对作业指导书进行多维度智能评分。

## 系统架构

```
📁 RAG评分系统
├── 🗂️ 向量知识库 (ChromaDB + Sentence-Transformers)
├── 🤖 VLLM推理服务 (部署的大语言模型)  
├── ⚖️ 智能评分引擎 (多维度评分逻辑)
└── 📊 评分报告生成 (JSON格式详细报告)
```

## 评分维度

系统对文档进行5个维度的评分：

| 评分项 | 权重 | 满分 | 评估内容 |
|--------|------|------|----------|
| **结构完整性** | 20% | 20分 | 必需章节覆盖、层级逻辑、章节组织 |
| **内容完整性** | 30% | 30分 | 技术准确性、职责完整性、作业指引质量 |
| **技术准确性** | 25% | 25分 | 技术参数、专业术语、技术要求可执行性 |
| **安全合规性** | 15% | 15分 | 风险识别、防护措施、应急处置流程 |
| **语法规范性** | 10% | 10分 | 语法错误、表达规范、用词准确性 |

**总分：100分**

## 前置条件

### 1. 环境准备
```bash
# Python环境
python >= 3.9

# 依赖安装
pip install sentence-transformers chromadb openai backoff
```

### 2. 知识库准备
```bash
# 如果知识库为空，先添加文档
python quick_reindex.py
```

### 3. VLLM服务
确保VLLM服务正在运行：
```bash
# 默认地址: http://localhost:8000/v1
# 默认模型: qwen2.5-vl-3b
```

## 快速开始

### 1. 简单测试
```bash
# 测试系统连接和功能
python test_vllm_scoring.py

# 指定VLLM服务地址
python test_vllm_scoring.py http://your-vllm-server:8000/v1 your-model-name
```

### 2. 评分已索引文档
```bash
# 评分知识库中的文档
python run_complete_rag_scoring.py score-kb

# 评分指定文档
python run_complete_rag_scoring.py score-kb "场景1(1).pdf"
```

### 3. 评分新文档
```bash
# 评分单个文件
python run_complete_rag_scoring.py score data/raw/场景1(1).pdf

# 批量评分目录中的PDF文件
python run_complete_rag_scoring.py batch data/raw/
```

### 4. 系统测试
```bash
# 测试各组件连接
python run_complete_rag_scoring.py test
```

## 使用示例

### 示例1：评分现有文档
```bash
$ python test_vllm_scoring.py
🤖 测试VLLM连接...
✅ VLLM连接成功！
📝 响应示例: 你好！我是一个AI助手...

📚 初始化知识库...
   知识库状态: 1 个文档, 107 个文档块
⚖️  初始化评分引擎...
📄 准备评分文档: 场景1(1).pdf
🚀 开始执行RAG智能评分...
✅ 评分完成！耗时: 45.23 秒

📊 评分结果汇总
========================================
📄 文档: 场景1(1).pdf
🎯 总分: 73/100 (73.0%)
🏆 等级: 中等
```

### 示例2：完整评分流程
```bash
$ python run_complete_rag_scoring.py score-kb
🚀 RAG智能评分系统启动
📚 初始化RAG知识库...
✅ 知识库已初始化: 1 个文档, 107 个文档块
🤖 初始化VLLM客户端...
✅ VLLM连接测试成功
⚖️  初始化RAG评分引擎...
✅ RAG评分引擎已初始化

📚 评分知识库文档: (第一个文档)
⚖️  开始对知识库文档 '场景1(1).pdf' 进行RAG评分...
✅ 结构完整性: 16/20
✅ 内容完整性: 22/30  
✅ 技术准确性: 18/25
✅ 安全合规性: 11/15
✅ 语法规范性: 8/10
📊 评分报告已保存: output/rag_scoring_reports/rag_scoring_report_...
```

## 评分报告格式

系统生成的JSON评分报告包含以下信息：

```json
{
  "document_info": {
    "file_name": "场景1(1).pdf",
    "scene_type": "scenario_one", 
    "scene_name": "作业指导书",
    "total_pages": 12
  },
  "scoring_timestamp": "2025-08-04T15:30:45.123456",
  "scoring_method": "RAG-based dynamic retrieval",
  "summary": {
    "total_score": 75,
    "max_total_score": 100,
    "percentage": 75.0,
    "grade": "中等",
    "scoring_criteria_count": 5
  },
  "detailed_scores": {
    "structure_completeness": {
      "name": "结构完整性",
      "score": 16,
      "max_score": 20,
      "reasoning": "文档包含了基本的必需章节...",
      "evaluation_focus": "文档章节结构、必需部分的完整性",
      "context_used": "检索到的相关内容...",
      "context_length": 1234
    }
    // ... 其他评分项
  },
  "score_breakdown": {
    // 各项权重计算详情
  }
}
```

## 系统特点

### ✅ 优势
- **智能检索**：基于语义相似度动态检索相关内容
- **多维评分**：5个维度全面评估文档质量
- **可解释性**：每项评分都有详细推理过程
- **灵活配置**：支持自定义评分标准和权重
- **批量处理**：支持单文档和批量文档评分
- **结果可视**：生成详细的JSON格式评分报告

### ⚙️ 技术亮点
- **RAG架构**：结合检索和生成，提高评分准确性
- **向量数据库**：使用ChromaDB高效存储和检索文档块
- **语义理解**：基于Sentence-Transformers的语义检索
- **并行处理**：多线程并行执行各评分项，提高效率
- **错误恢复**：完善的异常处理和重试机制

## 配置说明

### 评分标准配置
在`src/inference/rag_scoring_engine.py`中可以调整：
- 各评分项的权重比例
- 满分设置
- 搜索查询关键词
- 上下文长度限制
- 相似度阈值

### VLLM连接配置
```python
# 默认配置
VLLM_BASE_URL = "http://localhost:8000/v1"
MODEL_NAME = "qwen2.5-vl-3b"
API_KEY = "EMPTY"
```

## 故障排除

### 常见问题

1. **知识库为空**
   ```bash
   # 重新索引文档
   python quick_reindex.py
   ```

2. **VLLM连接失败**
   ```bash
   # 检查服务状态
   curl http://localhost:8000/v1/models
   
   # 检查防火墙和网络
   telnet localhost 8000
   ```

3. **评分超时**
   - 调整`timeout`参数（默认120秒）
   - 检查VLLM服务性能
   - 减少`context_length`参数

4. **分数解析失败**
   - 检查LLM响应格式
   - 调整prompt模板
   - 查看日志中的详细错误信息

### 日志调试
```bash
# 设置调试级别
export PYTHONPATH=/path/to/project
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# 运行你的评分脚本
"
```

## 扩展开发

### 添加新的评分维度
1. 在`scoring_criteria`中添加配置
2. 实现对应的`_score_xxx_with_context`方法
3. 添加相应的prompt模板

### 自定义prompt模板
在`src/inference/prompts.py`中修改或添加新的prompt方法

### 集成其他LLM服务
继承`VLLMInferenceClient`类，实现不同的API调用逻辑

## 性能优化

- **并行处理**：默认3个线程并行执行评分项
- **缓存机制**：向量数据库自动缓存检索结果
- **批量推理**：可配置批量调用LLM API
- **上下文压缩**：动态调整上下文长度避免超限

---

💡 **提示**：首次使用建议先运行`test_vllm_scoring.py`进行系统测试，确保所有组件正常工作后再进行正式评分。