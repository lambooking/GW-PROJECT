# 文档批注功能 - 快速上手

## 一分钟快速开始

### 自动评分并生成批注文档

```bash
# 运行评分系统，自动生成批注文档
python run_complete_rag_scoring.py
```

输入您的文档路径后，系统会自动：
1. 解析文档
2. 执行RAG评分
3. **生成批注版文档** ← 新功能！
4. 生成HTML报告
5. 生成JSON报告

### 输出文件

```
output/
├── annotated_documents/              ← 新增批注文档目录
│   ├── 场景1_批注版.pdf             # PDF批注版
│   └── 场景1_批注报告.txt           # 文本批注报告
└── rag_scoring_reports/
    ├── html/场景1_report.html       # HTML评分报告
    └── 场景1_report.json             # JSON评分结果
```

## 功能特点

### ✅ 支持格式
- **PDF**: 文本批注、高亮、文本框
- **DOCX**: 内联批注、高亮、汇总页
- **DOC**: 通过转换支持

### ✅ 批注类型
- 🔴 **严重问题** (扣分≥5): 红色标记
- 🟡 **一般问题** (扣分2-5): 黄/橙色标记
- 🔵 **建议改进** (扣分<2): 蓝色标记

### ✅ 智能定位
- 坐标定位（精确到像素）
- 文本搜索定位（精确到段落）
- 章节名称定位（精确到章节）
- 智能推断定位（通用回退）

## 使用示例

### 示例1：命令行使用

```bash
# 评分并生成批注
python run_complete_rag_scoring.py

# 测试批注功能
python scripts/test_annotation.py
```

### 示例2：代码集成

```python
from run_complete_rag_scoring import RAGScoringSystem

# 初始化系统
system = RAGScoringSystem()
system.initialize_components()

# 评分并生成批注（一步完成）
result = system.score_document_from_file("data/raw/文档.pdf")

# 查看批注文档路径
print(f"批注文档: {result['annotated_document_path']}")
print(f"批注数量: {result['annotation_count']}")
```

### 示例3：单独使用批注功能

```python
from src.annotation import AnnotationManager

# 创建批注管理器
manager = AnnotationManager()

# 根据评分结果生成批注文档
annotated_file = manager.annotate_document(
    original_file="原文档.pdf",
    scoring_result=scoring_result,  # 评分结果
    output_path="批注版.pdf"
)
```

## 批注内容示例

每条批注包含：

```
【评分项名称】
扣分: X.X/Y.Y分

问题: 缺少必需的'记录文件'章节

修改建议: 建议添加'5 记录文件'章节，
并列出相关记录表格名称和编号
```

## 效果预览

### PDF批注效果
- 📍 图钉式文本批注
- 🎨 彩色高亮标记
- 📋 末尾批注汇总页

### DOCX批注效果
- 💬 内联批注段落
- 🎨 段落高亮着色
- 📄 文档末尾批注汇总

## 文档资源

| 文档 | 说明 |
|------|------|
| [ANNOTATION_USAGE.md](ANNOTATION_USAGE.md) | 完整使用说明 |
| [ANNOTATION_EXAMPLE.md](../ANNOTATION_EXAMPLE.md) | 详细代码示例 |
| [ANNOTATION_IMPLEMENTATION_SUMMARY.md](ANNOTATION_IMPLEMENTATION_SUMMARY.md) | 技术实现细节 |

## 常见问题

**Q: 批注文档在哪里？**  
A: `output/annotated_documents/` 目录

**Q: 如何调整批注严重程度？**  
A: 修改`src/annotation/manager.py`中的`_determine_severity`方法

**Q: 支持哪些文档格式？**  
A: PDF（完全支持）、DOCX（完全支持）、DOC（有限支持）

**Q: 批注定位不准确怎么办？**  
A: 可以手动指定坐标或文本片段来提高精度

## 技术支持

如有问题，请查看：
1. 详细文档（docs/ANNOTATION_*.md）
2. 测试脚本（scripts/test_annotation.py）
3. 代码示例（ANNOTATION_EXAMPLE.md）

---

**版本**: v1.0.0  
**更新**: 2025-10-13  
**状态**: ✅ 生产就绪


