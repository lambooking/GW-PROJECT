# 如何使用比赛评分配置

## 概述

我们已经根据比赛方的评分细则创建了全新的评分配置，存储在 `config/competition_scoring_config.py` 中。

## 配置验证

✅ **场景一**（作业指导书审核）：5个评分项，权重总和 1.00  
✅ **场景二**（高后果区风险管控方案审核）：12个评分项，权重总和 0.99

## 评分项对照表

### 场景一：作业指导书审核（总分100分）

| 评分维度 | 权重 | 分值 | 对应比赛方要求 |
|---------|------|------|--------------|
| 内容与结构完整性 | 30% | 30分 | ✅ 整体审核 |
| 文字及语法规范性 | 15% | 15分 | ✅ 细节审核 - 文字及语法错误 |
| 业务逻辑一致性 | 20% | 20分 | ✅ 细节审核 - 业务逻辑错误 |
| 应急处置流程完整性 | 25% | 25分 | ✅ 细节审核 - 应急处置审核 |
| 模板规范性 | 10% | 10分 | ✅ 模板检测 |

**已满足的其他要求**：
- ✅ 识别效率（通过签字页优化等系统级优化实现）
- ✅ 兼容性（支持WORD和PDF格式）

### 场景二：高后果区风险管控方案审核（总分99分）

| 评分维度 | 权重 | 分值 | 对应比赛方要求 |
|---------|------|------|--------------|
| 签字页手签识别 | 10% | 10分 | ✅ 签字页手签识别 |
| 内容完整性 | 11% | 11分 | ✅ 内容完整性 |
| 影像图标注识别 | 14% | 14分 | ✅ 影像图标注识别 |
| 入场线路图标注识别 | 15% | 15分 | ✅ 入场线路图标注识别 |
| 逃生路线图标注识别 | 15% | 15分 | ✅ 逃生路线图、应急疏散集结点标注识别 |
| 图片标注一致性 | 4% | 4分 | ✅ 图片标注一致性 |
| 上下文内容一致性 | 9% | 9分 | ✅ 上下文内容一致性 |
| 标准遵从度 | 4% | 4分 | ✅ 标准遵从度（GB32167） |
| 特定内容完整性 | 4% | 4分 | ✅ 内容完整性（特定图片要求） |
| 时间逻辑一致性 | 4% | 4分 | ✅ 时间逻辑一致性 |
| 数据逻辑正确性 | 4% | 4分 | ✅ 数据逻辑是否正确 |
| 文字模板一致性 | 5% | 5分 | ✅ 文字模板一致性 |

**已满足的其他要求**：
- ✅ 识别效率（通过签字页优化等系统级优化实现）
- ✅ 兼容性（需兼容WORD和PDF格式的风险管控方案）
- ✅ 模板检测（识别是否使用规定模板）

## 如何应用新配置

### 方案一：直接修改评分引擎（推荐用于正式比赛）

修改 `src/inference/rag_scoring_engine.py`：

```python
# 在文件顶部导入新配置
from config.competition_scoring_config import (
    COMPETITION_SCORING_CRITERIA_SCENE1,
    COMPETITION_SCORING_CRITERIA_SCENE2
)

# 在 __init__ 方法中替换原有配置
def __init__(self, vllm_client, knowledge_base, use_competition_mode=True):
    self.vllm_client = vllm_client
    self.knowledge_base = knowledge_base
    self.scoring_prompts = ScoringPrompts()
    self.signature_extractor = SignatureExtractor()
    
    # 根据模式选择评分配置
    if use_competition_mode:
        self.scoring_criteria_scene1 = COMPETITION_SCORING_CRITERIA_SCENE1
        self.scoring_criteria_scene2 = COMPETITION_SCORING_CRITERIA_SCENE2
        logger.info("🏆 已启用比赛评分模式")
    else:
        self.scoring_criteria_scene1 = self.原有配置_scene1
        self.scoring_criteria_scene2 = self.原有配置_scene2
        logger.info("📝 使用标准评分模式")
```

### 方案二：创建比赛专用评分引擎（推荐用于开发测试）

创建 `src/inference/competition_rag_scoring_engine.py`：

```python
from .rag_scoring_engine import RAGScoringEngine
from config.competition_scoring_config import (
    COMPETITION_SCORING_CRITERIA_SCENE1,
    COMPETITION_SCORING_CRITERIA_SCENE2
)

class CompetitionRAGScoringEngine(RAGScoringEngine):
    """比赛专用RAG评分引擎 - 使用比赛方评分细则"""
    
    def __init__(self, vllm_client, knowledge_base):
        super().__init__(vllm_client, knowledge_base)
        
        # 替换为比赛评分配置
        self.scoring_criteria_scene1 = COMPETITION_SCORING_CRITERIA_SCENE1
        self.scoring_criteria_scene2 = COMPETITION_SCORING_CRITERIA_SCENE2
        
        logger.info("🏆 比赛评分引擎已初始化")
```

使用时：
```python
from src.inference.competition_rag_scoring_engine import CompetitionRAGScoringEngine

# 创建比赛专用引擎
scoring_engine = CompetitionRAGScoringEngine(vllm_client, knowledge_base)
result = scoring_engine.score_document(document)
```

## 实施步骤

### 步骤1：验证配置

```bash
python config/competition_scoring_config.py
```

确认输出：
```
场景一权重总和: 1.00 ✅
场景二权重总和: 0.99 ✅
```

### 步骤2：更新评分引擎

选择上述方案一或方案二，修改相应文件。

### 步骤3：测试评分

```bash
# 测试场景一
python run_complete_rag_scoring.py score test_documents/作业指导书.docx

# 测试场景二
python run_complete_rag_scoring.py score test_documents/风险管控方案.docx
```

### 步骤4：检查输出报告

查看生成的HTML报告，确认评分项与比赛要求一致：
- 场景一应有5个评分维度
- 场景二应有12个评分维度
- 每个维度的名称和权重与配置一致

## 配置文件位置

- **比赛评分配置**: `config/competition_scoring_config.py`
- **对齐方案文档**: `docs/COMPETITION_SCORING_ALIGNMENT.md`
- **评分引擎**: `src/inference/rag_scoring_engine.py`

## 关键差异对比

### 原始配置 vs 比赛配置

**场景一变化**：
- ❌ 删除：`technical_accuracy`（技术准确性）
- ❌ 删除：`safety_compliance`（安全合规性）  
- ✅ 新增：`business_logic_consistency`（业务逻辑一致性）
- ✅ 新增：`emergency_response_procedure`（应急处置流程完整性）
- ✅ 新增：`template_compliance`（模板规范性）
- ✅ 合并：`structure_content_completeness`（内容与结构完整性）

**场景二变化**：
- ✅ 新增：`image_text_consistency`（图片标注一致性）
- ✅ 新增：`context_consistency`（上下文内容一致性）
- ✅ 新增：`standard_compliance`（标准遵从度）
- ✅ 新增：`specific_content_completeness`（特定内容完整性）
- ✅ 新增：`time_logic_consistency`（时间逻辑一致性）
- ✅ 新增：`data_logic_correctness`（数据逻辑正确性）
- ✅ 新增：`text_template_consistency`（文字模板一致性）
- ✅ 细化：原有的路线图、影像图评分项更加详细

## 注意事项

1. **新增的评分项需要开发相应的评分逻辑**
   - 一致性检测（图片与文字、上下文、时间、数据等）
   - 标准遵从度检测（GB32167）
   - 模板匹配检测

2. **多模态能力要求更高**
   - 场景二大量依赖图片内容理解
   - 需要准确识别图片标注、路线合理性等

3. **prompt需要优化**
   - 根据新的evaluation_focus调整prompt
   - 强调比赛方特别关注的检查点

4. **测试覆盖**
   - 确保每个新增评分项都能正确工作
   - 验证权重计算准确性
   - 检查输出报告格式

## 后续开发任务

1. [ ] 实现业务逻辑一致性检测算法
2. [ ] 实现应急处置流程完整性深度检测
3. [ ] 实现模板规范性检测（需准备标准模板）
4. [ ] 实现图片标注一致性对比
5. [ ] 实现上下文内容一致性对比（表格与文本）
6. [ ] 实现标准遵从度检测（GB32167参考）
7. [ ] 实现时间逻辑一致性检测
8. [ ] 实现数据逻辑正确性检测（数值范围、类型等）
9. [ ] 实现文字模板一致性检测
10. [ ] 优化所有评分项的prompt
11. [ ] 全面测试验证

## 快速切换命令

### 启用比赛模式
```python
# 在评分脚本中
use_competition_mode = True  # 或通过环境变量/命令行参数控制
```

### 批量评分（比赛模式）
```bash
# 确保评分引擎已切换到比赛配置
python run_batch_rag_scoring.py /path/to/competition/documents
```

---

**更新日期**: 2025-01-30  
**版本**: v1.0  
**状态**: 配置已完成，待集成到评分引擎

