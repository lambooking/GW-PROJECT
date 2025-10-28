# RAG 智能评分系统使用指南

## 📋 目录

- [支持的文件格式](#支持的文件格式)
- [快速开始](#快速开始)
- [命令详解](#命令详解)
- [使用示例](#使用示例)
- [输出说明](#输出说明)
- [常见问题](#常见问题)
- [注意事项](#注意事项)

---

## 支持的文件格式

系统支持三种常见的文档格式，每种格式都有其特定的解析引擎和能力：

### 📄 PDF 格式

**解析引擎**: PyMuPDF (fitz)

**支持功能**:
- ✅ 文本提取（支持多列布局）
- ✅ 表格提取（基础支持）
- ✅ 图片提取（包括位置信息）
- ✅ 页码信息
- ✅ 坐标定位

**适用场景**: 
- 扫描文档
- 正式发布的文档
- 包含复杂格式的文档

### 📝 DOCX 格式

**解析引擎**: python-docx

**支持功能**:
- ✅ 段落文本提取
- ✅ 表格提取（完整支持）
- ✅ 图片提取
- ✅ 标题层级识别
- ✅ 样式信息

**适用场景**:
- Word 编辑的文档
- 结构化程度高的文档
- 需要识别标题层级的文档

### 📃 DOC 格式（旧版 Word）

**解析引擎**: antiword（命令行工具）

**支持功能**:
- ✅ 文本提取
- ⚠️ 表格提取（不支持）
- ⚠️ 图片提取（不支持）
- ⚠️ 格式信息（有限）

**前置要求**: 需要系统安装 `antiword` 工具

**安装方法**:
```bash
# Ubuntu/Debian
sudo apt-get install antiword

# CentOS/RHEL
sudo yum install antiword

# macOS
brew install antiword
```

**建议**: 如果可能，请将 .doc 文件转换为 .docx 格式以获得更好的解析效果。

---

## 快速开始

### 1️⃣ 环境准备

确保已安装所有依赖：

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# （可选）安装 antiword 以支持 .doc 格式
# 参见上面的安装说明
```

### 2️⃣ 启动 VLLM 服务

评分系统需要 VLLM 服务运行：

```bash
# 使用提供的启动脚本
bash scripts/start_vllm.sh

# 或手动启动
python -m vllm.entrypoints.openai.api_server \
    --model qwen2.5-vl-3b \
    --port 8000
```

验证 VLLM 服务：
```bash
curl http://localhost:8000/health
```

### 3️⃣ 初始化知识库

首次使用前，建议添加参考文档到知识库：

```bash
python quick_reindex.py
```

### 4️⃣ 测试系统

验证所有组件正常工作：

```bash
python run_complete_rag_scoring.py test
```

---

## 命令详解

### `test` - 测试系统连接

测试 VLLM 服务连接和系统组件初始化。

```bash
python run_complete_rag_scoring.py test
```

**输出示例**:
```
🚀 RAG智能评分系统启动
📚 初始化RAG知识库...
✅ 知识库已初始化: 5 个文档, 342 个文档块
🤖 初始化VLLM客户端 (http://localhost:8000/v1)...
✅ VLLM连接测试成功
🎉 所有组件初始化完成！
```

---

### `score <file>` - 评分单个文件

对指定的文档文件进行智能评分。

```bash
python run_complete_rag_scoring.py score <文件路径>
```

**支持的文件格式**: `.pdf`, `.docx`, `.doc`

**处理流程**:
1. 文档解析（提取文本、表格、图片）
2. 场景识别（自动判断是场景一或场景二）
3. RAG 增强评分（结合知识库）
4. 生成评分报告（JSON + HTML）

**示例**:
```bash
# 评分 PDF 文件
python run_complete_rag_scoring.py score data/raw/场景1\(1\).pdf

# 评分 DOCX 文件
python run_complete_rag_scoring.py score documents/instruction.docx

# 评分 DOC 文件（需要安装 antiword）
python run_complete_rag_scoring.py score documents/old_format.doc
```

---

### `score-kb [name]` - 评分知识库中的文档

对已添加到知识库的文档进行评分，无需重新解析。

```bash
python run_complete_rag_scoring.py score-kb [文档名称]
```

**参数说明**:
- `文档名称`: 可选，如果不指定则评分第一个文档

**示例**:
```bash
# 评分知识库中的第一个文档
python run_complete_rag_scoring.py score-kb

# 评分指定名称的文档
python run_complete_rag_scoring.py score-kb "场景1(1).pdf"
```

---

### `batch <dir>` - 批量评分

批量评分指定目录下的所有 PDF 文件。

```bash
python run_complete_rag_scoring.py batch <目录路径>
```

**功能特点**:
- 自动扫描目录中的所有 PDF 文件
- 逐个处理并生成独立报告
- 生成批量评分汇总报告
- 错误处理：单个文件失败不影响其他文件

**示例**:
```bash
# 批量评分 data/raw 目录下的所有 PDF
python run_complete_rag_scoring.py batch data/raw/

# 批量评分当前目录下的 PDF
python run_complete_rag_scoring.py batch ./
```

**输出**:
- 每个文档的独立 JSON 报告
- 每个文档的独立 HTML 报告
- 批量汇总报告 `batch_scoring_summary_YYYYMMDD_HHMMSS.json`

---

### `html-convert` - 转换 JSON 报告为 HTML

将已生成的 JSON 评分报告批量转换为 HTML 格式。

```bash
python run_complete_rag_scoring.py html-convert
```

**使用场景**:
- 重新生成 HTML 报告
- HTML 生成失败后的补救
- 报告模板更新后批量重新生成

**示例**:
```bash
python run_complete_rag_scoring.py html-convert
```

---

## 使用示例

### 示例 1: 评分 PDF 文件

```bash
# 评分作业指导书 PDF
python run_complete_rag_scoring.py score data/raw/场景1\(1\).pdf
```

**预期输出**:
```
🚀 RAG智能评分系统启动
📚 初始化RAG知识库...
✅ 知识库已初始化: 5 个文档, 342 个文档块
📄 开始评分文档: data/raw/场景1(1).pdf
🔄 正在预处理文档...
✅ 文档预处理完成: 145 个文本段落, 8 个表格
⚖️  开始RAG智能评分...
📊 JSON评分报告已保存: output/rag_scoring_reports/rag_scoring_report_场景1(1)_2025-10-22T14-30-15.json
🌐 HTML评分报告已生成: output/rag_scoring_reports/html/rag_scoring_report_场景1(1)_2025-10-22T14-30-15.html

============================================================
📊 RAG智能评分报告摘要
============================================================
📄 文档信息:
   - 文件名: 场景1(1).pdf
   - 场景类型: 作业指导书
   - 总页数: 12

🎯 总体评分:
   - 总分: 82.5/100
   - 得分率: 82.5%
   - 等级: B

📋 各项评分:
   结构完整性: 18/20 (权重: 20.0%, 加权分: 18.0)
   内容完整性: 25/30 (权重: 30.0%, 加权分: 25.0)
   引用文件可追溯性: 13/15 (权重: 15.0%, 加权分: 13.0)
   业务逻辑: 16/20 (权重: 20.0%, 加权分: 16.0)
   语法语句: 10.5/15 (权重: 15.0%, 加权分: 10.5)
============================================================
```

---

### 示例 2: 评分 DOCX 文件

```bash
# 评分 Word 文档
python run_complete_rag_scoring.py score documents/管道巡检指导书.docx
```

**处理特点**:
- 自动识别标题层级（基于 Word 样式）
- 完整提取表格结构
- 提取嵌入图片

---

### 示例 3: 评分 DOC 文件（旧版 Word）

```bash
# 评分旧版 Word 文档
python run_complete_rag_scoring.py score documents/legacy_document.doc
```

**注意事项**:
1. 需要系统安装 `antiword` 工具
2. 无法提取表格和图片
3. 格式信息有限

**如果未安装 antiword**，会看到如下错误：
```
❌ .doc 文件需要 antiword 工具支持。请安装:
  Ubuntu/Debian: sudo apt-get install antiword
  CentOS/RHEL: sudo yum install antiword
或者将文件转换为 .docx 格式
```

---

### 示例 4: 批量评分混合格式文件

虽然 `batch` 命令默认只处理 PDF，但你可以手动处理混合格式：

```bash
# 创建一个简单的批量处理脚本
for file in documents/*.{pdf,docx}; do
    if [ -f "$file" ]; then
        echo "评分: $file"
        python run_complete_rag_scoring.py score "$file"
    fi
done
```

---

## 输出说明

### JSON 报告

**位置**: `output/rag_scoring_reports/`

**命名格式**: `rag_scoring_report_<文档名>_<时间戳>.json`

**内容结构**:
```json
{
  "document_info": {
    "file_name": "场景1(1).pdf",
    "scene_type": "scenario_one",
    "scene_name": "作业指导书",
    "total_pages": 12,
    "classification_confidence": 0.95
  },
  "summary": {
    "total_score": 82.5,
    "max_total_score": 100,
    "percentage": 82.5,
    "grade": "B"
  },
  "detailed_scores": {
    "structure_completeness": {
      "name": "结构完整性",
      "score": 18,
      "max_score": 20,
      "reasoning": "文档结构完整，包含所需的各个章节..."
    },
    // ... 更多评分项
  },
  "score_breakdown": {
    "structure_completeness": {
      "weight": 0.2,
      "weighted_score": 18.0
    },
    // ... 更多评分细节
  }
}
```

---

### HTML 报告

**位置**: `output/rag_scoring_reports/html/`

**命名格式**: `rag_scoring_report_<文档名>_<时间戳>.html`

**特点**:
- 📊 可视化评分图表
- 📝 详细的评分说明
- 🎨 美观的 UI 设计
- 🖨️ 可打印格式
- 🌐 可在浏览器中直接查看

**打开方式**:
```bash
# macOS
open output/rag_scoring_reports/html/rag_scoring_report_*.html

# Linux
xdg-open output/rag_scoring_reports/html/rag_scoring_report_*.html

# Windows
start output/rag_scoring_reports/html/rag_scoring_report_*.html
```

---

### 评分结果解读

#### 评分等级

| 等级 | 分数范围 | 说明 |
|------|---------|------|
| **A** | 90-100 | 优秀，文档质量高，完全符合要求 |
| **B** | 80-89 | 良好，文档质量较好，有小幅改进空间 |
| **C** | 70-79 | 合格，文档基本符合要求，需要改进 |
| **D** | 60-69 | 较差，文档存在明显问题，需要重大改进 |
| **F** | 0-59 | 不合格，文档质量不达标 |

#### 场景一评分项（作业指导书）

| 评分项 | 权重 | 最大分值 | 评估重点 |
|--------|------|---------|----------|
| 结构完整性 | 20% | 20 | 文档结构、章节完整性、目录 |
| 内容完整性 | 30% | 30 | 内容详细度、覆盖面、准确性 |
| 引用文件可追溯性 | 15% | 15 | 引用标准的真实性和有效性 |
| 业务逻辑 | 20% | 20 | 流程合理性、逻辑连贯性 |
| 语法语句 | 15% | 15 | 语法错误、表达规范性 |

#### 场景二评分项（高后果区风险管控方案）

| 评分项 | 权重 | 最大分值 | 评估重点 |
|--------|------|---------|----------|
| 图像识别 | 40% | 40 | 图像内容识别、分析准确性 |
| 上下文逻辑 | 45% | 45 | 文档逻辑一致性、前后关联 |
| 处理效率 | 15% | 15 | 处理速度、资源使用 |

---

## 常见问题

### Q1: 如何知道系统支持哪些格式？

系统自动检测文件扩展名，支持的格式包括：
- `.pdf` - PDF 文档
- `.docx` - Word 2007+ 文档
- `.doc` - Word 97-2003 文档（需要 antiword）

不支持的格式会返回明确的错误信息。

---

### Q2: DOC 格式解析失败怎么办？

**问题**: 提示需要 antiword 工具

**解决方案**:

**方案 1: 安装 antiword（推荐）**
```bash
# Ubuntu/Debian
sudo apt-get install antiword

# CentOS/RHEL
sudo yum install antiword

# macOS
brew install antiword
```

**方案 2: 转换为 DOCX 格式**
```bash
# 使用 LibreOffice 命令行转换
libreoffice --headless --convert-to docx document.doc

# 或使用在线转换工具
# 然后评分 DOCX 文件
python run_complete_rag_scoring.py score document.docx
```

---

### Q3: VLLM 服务连接失败

**症状**: 提示 "VLLM连接测试失败"

**排查步骤**:

1. **检查 VLLM 服务是否运行**
   ```bash
   curl http://localhost:8000/health
   ```

2. **查看 VLLM 服务状态**
   ```bash
   ps aux | grep vllm
   ```

3. **重启 VLLM 服务**
   ```bash
   # 停止现有服务
   pkill -f vllm
   
   # 重新启动
   bash scripts/start_vllm.sh
   ```

4. **检查端口占用**
   ```bash
   lsof -i :8000
   ```

5. **修改配置（如果使用不同端口）**
   编辑 `run_complete_rag_scoring.py`：
   ```python
   system = RAGScoringSystem(
       vllm_base_url="http://localhost:8001/v1",  # 修改端口
       vllm_model="qwen2.5-vl-3b"
   )
   ```

---

### Q4: 知识库为空的警告

**症状**: 提示 "⚠️ 知识库为空，建议先运行 quick_reindex.py 添加文档"

**影响**: 评分仍可进行，但缺少 RAG 增强（无法参考知识库）

**解决方案**:
```bash
# 初始化知识库
python quick_reindex.py

# 或手动添加文档
# （这需要使用新的 CLI 工具）
./ragcli kb add data/raw/场景1\(1\).pdf
```

---

### Q5: 文件格式不支持怎么办？

**症状**: 提示 "Unsupported file format"

**解决方案**:

1. **检查文件扩展名是否正确**
   ```bash
   file document.pdf  # 查看实际文件类型
   ```

2. **转换为支持的格式**
   - TXT → 复制内容到 DOCX
   - RTF → 另存为 DOCX
   - HTML → 打印为 PDF

3. **确保文件完整性**
   ```bash
   # 检查文件是否损坏
   pdfinfo document.pdf  # 对于 PDF
   ```

---

### Q6: 文件太大无法处理

**问题**: 提示 "File too large"

**默认限制**: 50MB

**解决方案**:

1. **压缩 PDF 文件**
   ```bash
   # 使用 Ghostscript 压缩
   gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 \
      -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH \
      -sOutputFile=output.pdf input.pdf
   ```

2. **修改文件大小限制**
   编辑 `src/data/parsers/base.py`：
   ```python
   def _validate_file_size(self, file_path: Path, max_size_mb: int = 100):
       # 将 50 改为 100 或更大
   ```

3. **分割大文件**
   ```bash
   # 使用 pdftk 分割 PDF
   pdftk input.pdf burst
   ```

---

### Q7: 评分结果看起来不准确

**可能原因**:
1. 文档解析不完整
2. 知识库内容不足
3. VLLM 模型推理问题

**排查方法**:

1. **检查文档解析日志**
   ```bash
   tail -f logs/rag_scoring_*.log
   ```

2. **查看 JSON 报告中的详细信息**
   ```bash
   cat output/rag_scoring_reports/rag_scoring_report_*.json | jq
   ```

3. **检查知识库内容**
   ```bash
   # 使用新 CLI 查询知识库
   ./ragcli kb list
   ```

4. **重新索引知识库**
   ```bash
   python quick_reindex.py
   ```

---

### Q8: 批量评分时部分文件失败

**行为**: 批量评分会继续处理其他文件

**查看失败原因**:
```bash
# 查看批量汇总报告
cat output/rag_scoring_reports/batch_scoring_summary_*.json | jq '.results[] | select(.success == false)'
```

**常见失败原因**:
- 文件损坏
- 格式不支持
- 文件大小超限
- 内容解析错误

---

## 注意事项

### 文件大小限制

- **默认最大文件大小**: 50MB
- **建议文件大小**: < 20MB
- **超大文件**: 考虑分割处理

### 支持的文件编码

- **PDF**: 自动处理各种编码
- **DOCX**: UTF-8（Word 默认）
- **DOC**: 依赖 antiword 的编码支持

**中文支持**: 所有格式都完全支持中文

### 最佳实践建议

#### 1. 文档准备

✅ **推荐做法**:
- 使用清晰的文档结构
- 表格使用标准格式
- 图片嵌入文档而非链接
- 文件名使用有意义的命名

❌ **避免**:
- 过度复杂的排版
- 大量高分辨率图片
- 嵌套过深的表格
- 特殊字符和表情符号

#### 2. 格式选择

| 场景 | 推荐格式 | 原因 |
|------|---------|------|
| 新建文档 | DOCX | 完整支持，解析准确 |
| 扫描文档 | PDF | OCR 支持好 |
| 旧文档 | 转 DOCX | 避免 DOC 限制 |
| 长文档 | PDF | 性能更好 |

#### 3. 性能优化

- **并行处理**: 使用 `batch` 命令而非循环
- **知识库预热**: 提前初始化知识库
- **日志管理**: 定期清理日志文件
- **报告归档**: 定期备份和清理报告

#### 4. 错误处理

```bash
# 添加错误处理的批量脚本示例
#!/bin/bash
for file in documents/*.pdf; do
    echo "Processing: $file"
    if python run_complete_rag_scoring.py score "$file" 2>&1 | tee -a batch.log; then
        echo "✅ Success: $file"
    else
        echo "❌ Failed: $file"
        echo "$file" >> failed_files.txt
    fi
done
```

#### 5. 评分准确性提升

1. **充实知识库**: 添加更多参考文档
   ```bash
   python quick_reindex.py
   ```

2. **保持模型更新**: 使用最新的 VLLM 模型

3. **提供高质量输入**: 清晰、结构化的文档

4. **定期校准**: 对比人工评分结果

#### 6. 安全性考虑

- **敏感信息**: 评分前检查文档是否包含敏感信息
- **文件来源**: 确保文档来源可信
- **权限控制**: 限制输出目录访问权限
- **日志审计**: 定期审查评分日志

---

## 快速命令参考

```bash
# 测试系统
python run_complete_rag_scoring.py test

# 评分单个文件
python run_complete_rag_scoring.py score document.pdf
python run_complete_rag_scoring.py score document.docx
python run_complete_rag_scoring.py score document.doc

# 快捷方式（直接传文件路径）
python run_complete_rag_scoring.py document.pdf

# 批量评分
python run_complete_rag_scoring.py batch data/raw/

# 知识库文档评分
python run_complete_rag_scoring.py score-kb

# 转换报告
python run_complete_rag_scoring.py html-convert

# 查看帮助
python run_complete_rag_scoring.py
```

---

## 进阶用法

### 自定义 VLLM 配置

编辑 `run_complete_rag_scoring.py` 修改 VLLM 设置：

```python
system = RAGScoringSystem(
    vllm_base_url="http://your-server:8000/v1",
    vllm_model="your-model-name"
)
```

### 编程方式调用

```python
from run_complete_rag_scoring import RAGScoringSystem

# 创建系统实例
system = RAGScoringSystem()

# 初始化组件
system.initialize_components()

# 评分文档
result = system.score_document_from_file("document.pdf")

# 访问评分结果
print(f"总分: {result['summary']['total_score']}")
print(f"等级: {result['summary']['grade']}")
```

---

## 故障排除清单

遇到问题时，请按以下顺序检查：

- [ ] VLLM 服务是否运行（`curl http://localhost:8000/health`）
- [ ] 文件路径是否正确（使用绝对路径测试）
- [ ] 文件格式是否支持（`.pdf`, `.docx`, `.doc`）
- [ ] 文件大小是否超限（默认 50MB）
- [ ] DOC 文件是否安装 antiword
- [ ] Python 依赖是否完整安装
- [ ] 日志文件中的详细错误信息
- [ ] 输出目录是否有写权限

---

## 获取帮助

如果以上内容无法解决您的问题：

1. **查看日志**: `logs/rag_scoring_*.log`
2. **查看技术文档**: `docs/` 目录下的其他文档
3. **提交 Issue**: 在项目仓库提交问题报告
4. **联系支持**: 通过项目维护者获取帮助

---

**📝 文档版本**: v1.0  
**📅 最后更新**: 2025-10-22  
**👤 维护者**: RAG 智能评分系统团队

