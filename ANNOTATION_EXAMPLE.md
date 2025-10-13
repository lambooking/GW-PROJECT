# 文档批注功能演示示例

## 快速开始示例

### 示例1：自动评分并生成批注文档

这是最简单的使用方式，评分和批注一步完成：

```python
#!/usr/bin/env python3
"""
完整示例：评分并生成批注文档
"""
from pathlib import Path
from run_complete_rag_scoring import RAGScoringSystem

# 1. 初始化评分系统
system = RAGScoringSystem(
    vllm_base_url="http://localhost:8000/v1",
    vllm_model="qwen2.5-vl-3b"
)

# 2. 初始化组件
if not system.initialize_components():
    print("系统初始化失败")
    exit(1)

# 3. 对文档进行评分（自动生成批注）
scoring_result = system.score_document_from_file(
    "data/raw/场景1(1).pdf"
)

# 4. 查看结果
print(f"\n总分: {scoring_result['summary']['total_score']}")
print(f"批注数量: {scoring_result.get('annotation_count', 0)}")
print(f"批注文档: {scoring_result.get('annotated_document_path', 'N/A')}")

# 输出示例：
# 总分: 73.5
# 批注数量: 5
# 批注文档: output/annotated_documents/场景1(1)_批注版.pdf
```

### 示例2：单独使用批注功能

如果你已经有了评分结果，想单独生成批注文档：

```python
from pathlib import Path
from src.annotation import AnnotationManager

# 假设这是你的评分结果
scoring_result = {
    "document_info": {
        "file_name": "作业指导书.pdf",
        "scene_type": "scenario_1"
    },
    "summary": {
        "total_score": 75.0,
        "max_total_score": 100.0
    },
    "detailed_scores": {
        "structure_completeness": {
            "name": "结构完整性",
            "score": 15,
            "max_score": 20,
            "reasoning": "文档缺少'记录文件'章节，建议补充相关记录表格清单。"
        },
        "technical_accuracy": {
            "name": "技术准确性",
            "score": 17,
            "max_score": 25,
            "reasoning": "技术参数表中部分数据不完整，缺少管径规格详细信息。"
        }
    }
}

# 创建批注管理器
manager = AnnotationManager()

# 生成批注文档
annotated_file = manager.annotate_document(
    original_file="data/raw/作业指导书.pdf",
    scoring_result=scoring_result,
    output_path="output/作业指导书_批注版.pdf"
)

print(f"批注文档已生成: {annotated_file}")
```

### 示例3：手动创建自定义批注

完全控制批注内容和位置：

```python
from src.annotation import (
    Annotation, 
    AnnotationSeverity, 
    AnnotationType,
    PdfAnnotator,
    DocxAnnotator
)

# 创建批注列表
annotations = [
    # 批注1：严重问题 - 缺少关键章节
    Annotation(
        location="文档结构",
        page_number=1,
        annotation_type=AnnotationType.COMMENT,
        severity=AnnotationSeverity.CRITICAL,
        score_item="结构完整性",
        content="文档缺少'5 记录文件'章节",
        suggestion="建议添加'5 记录文件'章节，并列出相关的记录表格名称和编号",
        score_lost=5.0,
        max_score=20.0,
        section_name="目录"
    ),
    
    # 批注2：一般问题 - 技术参数不完整
    Annotation(
        location="第3页 技术参数表",
        page_number=3,
        annotation_type=AnnotationType.HIGHLIGHT,
        severity=AnnotationSeverity.WARNING,
        score_item="技术准确性",
        content="技术参数表中缺少管径、壁厚等关键数据",
        suggestion="建议补充完整的管径(mm)、材质、壁厚(mm)、操作压力(MPa)等参数",
        score_lost=3.5,
        max_score=25.0,
        text_snippet="表1 技术参数",
        coordinates={"x0": 50, "y0": 200, "x1": 550, "y1": 350}
    ),
    
    # 批注3：建议改进 - 语法优化
    Annotation(
        location="第5页 第2段",
        page_number=5,
        annotation_type=AnnotationType.SUGGESTION,
        severity=AnnotationSeverity.INFO,
        score_item="语法规范性",
        content="部分表述可以更加规范和专业",
        suggestion="建议使用标准的技术术语，统一表述风格",
        score_lost=1.0,
        max_score=10.0,
        text_snippet="管道处及时掌握险情动态"
    )
]

# 方式A：使用PDF批注器
pdf_annotator = PdfAnnotator()
pdf_output = pdf_annotator.annotate(
    input_file="原文档.pdf",
    annotations=annotations,
    output_file="批注版.pdf"
)
print(f"PDF批注完成: {pdf_output}")

# 方式B：使用DOCX批注器
docx_annotator = DocxAnnotator()
docx_output = docx_annotator.annotate(
    input_file="原文档.docx",
    annotations=annotations,
    output_file="批注版.docx"
)
print(f"DOCX批注完成: {docx_output}")
```

### 示例4：批量处理多个文档

```python
from pathlib import Path
from run_complete_rag_scoring import RAGScoringSystem

# 初始化系统
system = RAGScoringSystem()
system.initialize_components()

# 获取所有待处理文档
documents = list(Path("data/raw").glob("*.pdf"))

print(f"找到 {len(documents)} 个文档待处理")

# 批量处理
results = []
for doc_path in documents:
    try:
        print(f"\n处理: {doc_path.name}")
        
        # 评分并生成批注
        result = system.score_document_from_file(str(doc_path))
        
        results.append({
            "file": doc_path.name,
            "score": result['summary']['total_score'],
            "annotations": result.get('annotation_count', 0),
            "annotated_file": result.get('annotated_document_path', 'N/A')
        })
        
        print(f"✅ 完成: {doc_path.name}")
        print(f"   得分: {result['summary']['total_score']}")
        print(f"   批注: {result.get('annotation_count', 0)} 条")
        
    except Exception as e:
        print(f"❌ 失败: {doc_path.name} - {e}")

# 生成汇总报告
print("\n" + "=" * 60)
print("批量处理汇总")
print("=" * 60)
for r in results:
    print(f"{r['file']}: {r['score']}分, {r['annotations']}条批注")
```

### 示例5：生成批注报告文本文件

```python
from src.annotation import AnnotationManager, Annotation, AnnotationSeverity

# 假设你有一批批注
annotations = [
    Annotation(
        location="第1页",
        page_number=1,
        annotation_type="comment",
        severity=AnnotationSeverity.CRITICAL,
        score_item="结构完整性",
        content="缺少必需章节",
        suggestion="补充缺失章节",
        score_lost=5.0,
        max_score=20.0
    ),
    # ... 更多批注
]

# 生成文本报告
manager = AnnotationManager()
report_file = manager.generate_annotation_report(
    annotations=annotations,
    output_path="output/批注汇总报告.txt"
)

print(f"批注报告已生成: {report_file}")

# 报告内容示例：
"""
============================================================
批注报告
============================================================

生成时间: 2025-10-13 14:30:00
总批注数: 5 条
  - 严重问题: 2 条
  - 一般问题: 2 条
  - 建议改进: 1 条

============================================================

严重问题 (2 条):
------------------------------------------------------------

1. [文档结构] 结构完整性
   页码: 第1页
   扣分: 5.0/20.0分
   问题: 文档缺少'5 记录文件'章节
   建议: 建议添加'5 记录文件'章节...

2. [第3页 技术参数表] 技术准确性
   页码: 第3页
   扣分: 8.0/25.0分
   问题: 技术参数表中缺少管径、壁厚等关键数据
   建议: 建议补充完整的管径...
...
"""
```

### 示例6：与评分引擎深度集成

```python
from src.inference.rag_scoring_engine import RAGScoringEngine
from src.inference.vllm_client import VLLMInferenceClient
from src.inference.rag_knowledge_base import RAGKnowledgeBase
from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
from src.annotation import AnnotationManager

# 1. 初始化组件
kb = RAGKnowledgeBase()
vllm = VLLMInferenceClient(base_url="http://localhost:8000/v1")
engine = RAGScoringEngine(vllm_client=vllm, knowledge_base=kb)
pipeline = PreprocessingPipeline()
ann_manager = AnnotationManager()

# 2. 处理文档
document = pipeline.process("data/raw/文档.pdf")

# 3. 评分（自动生成批注信息）
scoring_result = engine.score_document(document)

# scoring_result中包含：
# - detailed_scores: 各项评分详情
# - annotations: 自动生成的批注列表
# - annotation_count: 批注数量

# 4. 生成批注文档
annotated_file = ann_manager.annotate_document(
    original_file="data/raw/文档.pdf",
    scoring_result=scoring_result
)

print(f"批注文档: {annotated_file}")
print(f"批注数量: {len(scoring_result['annotations'])}")

# 5. 查看批注详情
for ann in scoring_result['annotations']:
    print(f"\n批注: {ann['score_item']}")
    print(f"  位置: {ann['location']}")
    print(f"  严重程度: {ann['severity']}")
    print(f"  扣分: {ann['score_lost']:.1f}分")
    print(f"  内容: {ann['content']}")
```

## 批注效果示例

### PDF批注效果

```
┌─────────────────────────────────────────┐
│  第1页                                  │
│                                         │
│  ┌──────────────────────────┐          │
│  │  作业指导书               │    🔴 [批注]│
│  │                          │    【结构完整性】│
│  │  1. 范围                 │    扣分: 5.0/20.0分│
│  │  2. 职责                 │    问题: 缺少必需章节│
│  │  3. 作业内容             │    建议: 补充记录文件│
│  │  4. 相关文件             │          │
│  │  [缺少: 5. 记录文件]     │          │
│  └──────────────────────────┘          │
│                                         │
│  ┌──────────────────────────┐          │
│  │  技术参数表 [高亮黄色]    │    🟡 [批注]│
│  │  管线名称: XXX           │    【技术准确性】│
│  │  长度: XXXkm             │    扣分: 3.5/25.0分│
│  │  [缺少管径、壁厚数据]     │    问题: 参数不完整│
│  └──────────────────────────┘          │
│                                         │
└─────────────────────────────────────────┘
```

### DOCX批注效果

```
作业指导书
━━━━━━━━━━━━━━━━━━━━━━

目录
1. 范围
2. 职责
3. 作业内容
4. 相关文件

💬 【结构完整性】扣分: 5.0/20.0分         ← 红色背景批注框
   问题: 文档缺少'5 记录文件'章节
   修改建议: 建议添加'5 记录文件'章节，并列出相关记录表格

━━━━━━━━━━━━━━━━━━━━━━

技术参数表 [黄色高亮]                     ← 高亮标记问题区域

💬 【技术准确性】扣分: 3.5/25.0分         ← 橙色背景批注框
   问题: 技术参数表中缺少管径、壁厚等关键数据
   修改建议: 建议补充完整的管径、材质、壁厚参数
```

## 常见使用场景

### 场景1：作业指导书评分

```python
# 针对作业指导书的常见批注类型
annotations_instruction_book = [
    # 结构问题
    Annotation(
        severity=AnnotationSeverity.CRITICAL,
        score_item="结构完整性",
        content="缺少必需的'记录文件'章节",
        suggestion="补充记录文件章节，列出检查表、记录表等"
    ),
    # 内容问题
    Annotation(
        severity=AnnotationSeverity.WARNING,
        score_item="内容完整性",
        content="操作步骤描述不够详细",
        suggestion="补充每个步骤的具体操作方法和注意事项"
    ),
    # 技术问题
    Annotation(
        severity=AnnotationSeverity.WARNING,
        score_item="技术准确性",
        content="技术参数表数据不完整",
        suggestion="补充管径、壁厚、操作压力等参数"
    )
]
```

### 场景2：风险管控方案评分

```python
# 针对风险管控方案的常见批注类型
annotations_risk_control = [
    # 图像问题
    Annotation(
        severity=AnnotationSeverity.CRITICAL,
        score_item="路线图完整性",
        content="缺少疏散路线图或路线图不清晰",
        suggestion="补充清晰的疏散路线图，标注入场线路、集合点"
    ),
    # HCA标注问题
    Annotation(
        severity=AnnotationSeverity.WARNING,
        score_item="HCA影像覆盖",
        content="HCA范围标注不清楚",
        suggestion="在影像图上明确标注高后果区边界和影响范围"
    ),
    # 签字问题
    Annotation(
        severity=AnnotationSeverity.CRITICAL,
        score_item="签字盖章完整性",
        content="缺少相关负责人签字",
        suggestion="补充编制人、审核人、批准人的完整签字"
    )
]
```

## 进阶技巧

### 技巧1：精确定位批注位置

```python
# 使用坐标精确定位（PDF）
annotation_with_coords = Annotation(
    location="第3页 右上角",
    page_number=3,
    coordinates={
        "x0": 400,  # 左边界
        "y0": 50,   # 上边界
        "x1": 550,  # 右边界
        "y1": 150   # 下边界
    },
    # ... 其他字段
)

# 使用文本片段定位（适用于所有格式）
annotation_with_text = Annotation(
    location="技术参数表",
    text_snippet="管线名称 管径 材质 壁厚",
    # ... 其他字段
)
```

### 技巧2：批注汇总页定制

PDF批注器会自动生成汇总页，你可以查看`pdf_annotator.py`中的`_add_summary_page`方法进行定制。

### 技巧3：批注样式定制

可以修改批注器的颜色和样式设置：

```python
# 在pdf_annotator.py中
def _get_color_for_severity(self, severity):
    # 自定义颜色
    colors = {
        AnnotationSeverity.CRITICAL: (0.9, 0.1, 0.1),  # 深红
        AnnotationSeverity.WARNING: (1.0, 0.5, 0.0),   # 橙色
        AnnotationSeverity.INFO: (0.2, 0.6, 1.0)       # 亮蓝
    }
    return colors.get(severity, (0, 0, 0))
```

## 总结

文档批注系统提供了三种使用层次：

1. **最简单**：使用`run_complete_rag_scoring.py`自动评分和批注
2. **灵活**：使用`AnnotationManager`根据评分结果生成批注
3. **完全控制**：手动创建`Annotation`对象，使用特定批注器

根据你的需求选择合适的方式即可！


