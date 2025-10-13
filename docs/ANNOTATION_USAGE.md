# 文档批注系统使用说明

## 概述

文档批注系统为RAG智能评分系统添加了在原文档上直接标注问题和修改建议的能力，支持PDF、DOCX、DOC等格式。

## 功能特性

### 1. 支持的文档格式

- **DOCX格式**: ✅ 完全支持
  - 在段落附近添加批注
  - 高亮问题区域
  - 自动生成批注汇总页
  
- **PDF格式**: ✅ 完全支持
  - 文本批注（图钉样式）
  - 高亮标记
  - 文本框批注
  - 批注汇总页

- **DOC格式**: ⚠️ 有限支持
  - 建议转换为DOCX后处理

### 2. 批注类型

- **评论批注** (Comment): 指出问题和不足
- **高亮标记** (Highlight): 突出显示问题区域
- **修改建议** (Suggestion): 提供具体的改进建议

### 3. 严重程度分级

- 🔴 **严重问题** (Critical): 扣分 ≥ 5分，红色标记
- 🟡 **一般问题** (Warning): 扣分 2-5分，黄色/橙色标记
- 🔵 **建议改进** (Info): 扣分 < 2分，蓝色标记

## 使用方法

### 方式一：通过主评分系统自动生成

使用`run_complete_rag_scoring.py`进行评分时，会自动生成批注版文档：

```bash
python run_complete_rag_scoring.py
```

评分完成后，批注版文档将保存在：
- 输出目录: `output/annotated_documents/`
- 文件名: `原文件名_批注版.pdf` 或 `原文件名_批注版.docx`
- 同时生成: `原文件名_批注报告.txt`（文本格式的批注汇总）

### 方式二：单独使用批注功能

```python
from src.annotation import AnnotationManager, Annotation, AnnotationSeverity

# 创建批注管理器
manager = AnnotationManager()

# 准备评分结果（包含批注信息）
scoring_result = {
    "annotations": [
        {
            "location": "第2页 第3段",
            "page_number": 2,
            "annotation_type": "comment",
            "severity": "warning",
            "score_item": "内容完整性",
            "content": "缺少详细的操作步骤说明",
            "suggestion": "建议补充具体的操作流程",
            "score_lost": 3.0,
            "max_score": 30.0
        }
    ],
    "scoring_details": {...}
}

# 生成批注文档
annotated_file = manager.annotate_document(
    original_file="data/raw/文档.pdf",
    scoring_result=scoring_result,
    output_path="output/文档_批注版.pdf"
)

print(f"批注文档已生成: {annotated_file}")
```

### 方式三：手动创建批注

```python
from src.annotation import Annotation, AnnotationSeverity, AnnotationType
from src.annotation.pdf_annotator import PdfAnnotator
from src.annotation.docx_annotator import DocxAnnotator

# 创建批注列表
annotations = [
    Annotation(
        location="第1页 技术参数表",
        page_number=1,
        annotation_type=AnnotationType.COMMENT,
        severity=AnnotationSeverity.CRITICAL,
        score_item="技术准确性",
        content="技术参数表中缺少管径规格信息",
        suggestion="建议补充完整的管径、材质、壁厚等技术参数",
        score_lost=8.0,
        max_score=25.0,
        coordinates={"x0": 100, "y0": 100, "x1": 400, "y1": 150}
    )
]

# 使用PDF批注器
annotator = PdfAnnotator()
annotated_file = annotator.annotate(
    input_file="原文档.pdf",
    annotations=annotations,
    output_file="批注版.pdf"
)
```

## 批注定位策略

系统采用多种策略自动定位批注位置：

### 1. 坐标定位（最精确）
- 使用文档解析时提取的坐标信息
- 适用于PDF格式

### 2. 文本搜索定位
- 通过文本片段匹配查找位置
- 适用于所有格式

### 3. 章节定位
- 根据章节名称定位
- 适用于结构化文档

### 4. 智能推断
- 根据评分项类型推断位置
  - 结构完整性 → 目录/章节
  - 技术准确性 → 技术参数表
  - 签字完整性 → 签字页（通常在末尾）

## 批注内容格式

每条批注包含以下信息：

```
【评分项名称】
扣分: X.X/Y.Y分

问题: [具体问题描述]

修改建议: [改进建议]
```

## 输出文件说明

### 1. 批注版文档
- DOCX: 在原文档基础上添加内联批注和高亮
- PDF: 添加批注标记和文本框，末尾附批注汇总页

### 2. 批注报告（.txt）
- 纯文本格式的批注汇总
- 按严重程度分类列出所有批注
- 便于快速浏览和打印

### 3. 目录结构

```
output/
├── annotated_documents/          # 批注文档目录
│   ├── 文档1_批注版.pdf
│   ├── 文档1_批注报告.txt
│   ├── 文档2_批注版.docx
│   └── 文档2_批注报告.txt
└── rag_scoring_reports/          # 评分报告目录
    ├── html/
    └── json/
```

## 测试批注功能

运行测试脚本验证批注功能：

```bash
python scripts/test_annotation.py
```

测试内容包括：
- 批注数据结构
- DOCX文档批注
- PDF文档批注
- 批注报告生成

## 技术实现细节

### DOCX批注实现
- 使用`python-docx`库
- 段落高亮 + 内联批注段落
- 支持颜色编码和样式设置

### PDF批注实现
- 使用`PyMuPDF (fitz)`库
- 支持多种批注类型：
  - Text Annotation (图钉式批注)
  - Highlight Annotation (高亮)
  - FreeText Annotation (文本框)
- 自动生成批注汇总页

## 注意事项

1. **PDF限制**: 
   - 加密的PDF可能无法添加批注
   - 扫描版PDF需要先进行OCR

2. **DOCX兼容性**:
   - 批注后的文档可用Microsoft Word和WPS打开
   - 某些复杂格式可能有显示差异

3. **DOC格式**:
   - 老旧的`.doc`格式支持有限
   - 建议转换为`.docx`格式后处理

4. **批注数量**:
   - 大量批注可能影响文档打开速度
   - PDF汇总页默认显示前20条批注

## 扩展和定制

### 自定义批注样式

```python
# 在docx_annotator.py中修改颜色
def _get_background_color(self, severity):
    if severity == AnnotationSeverity.CRITICAL:
        return "FF0000"  # 自定义红色
    # ...

# 在pdf_annotator.py中修改图标
def _add_text_annotation(self, page, point, annotation):
    text_annot = page.add_text_annot(
        point,
        annotation.get_formatted_content(),
        icon="Note"  # 可选: Comment, Note, Help, etc.
    )
```

### 添加新的批注类型

在`schemas.py`中扩展`AnnotationType`枚举：

```python
class AnnotationType(str, Enum):
    COMMENT = "comment"
    HIGHLIGHT = "highlight"
    SUGGESTION = "suggestion"
    MISSING = "missing"
    CUSTOM_TYPE = "custom_type"  # 新增自定义类型
```

## 常见问题

### Q: 批注文档无法打开？
A: 确保使用最新版本的PDF阅读器或Microsoft Office打开

### Q: 批注位置不准确？
A: 可以通过提供更准确的`coordinates`或`text_snippet`来改善定位

### Q: 中文显示乱码？
A: 检查系统是否安装了中文字体，PDF批注使用`china-s`字体

### Q: 如何调整批注密度？
A: 修改评分引擎中`_determine_annotation_severity`方法的阈值

## 更新日志

**v1.0.0** (2025-10-13)
- 初始版本发布
- 支持PDF和DOCX批注
- 集成到RAG评分系统
- 自动批注生成和定位

