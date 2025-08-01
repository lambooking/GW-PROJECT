"""
管理所有用于信息提取和评分的Prompt模板。
"""
import json
from typing import List

# 这是一个临时的解决方案，理想情况下应该从 src.data_processing.schemas 导入
# 但为了避免循环依赖，我们在这里定义一个简化的版本
class SimplifiedTextContent:
    def __init__(self, content: str, page_number: int):
        self.content = content
        self.page_number = page_number

class ExtractionPrompts:
    """
    封装了所有用于从文档中提取信息的Prompt模板。
    """

    def get_metadata_prompt(self, text_summary: str) -> str:
        """
        生成用于提取文档基础元数据的Prompt。

        Args:
            text_summary: 从文档中提取的文本摘要。

        Returns:
            一个格式化的Prompt字符串。
        """
        return f"""
请从以下文档内容中提取基础信息，并严格按照JSON格式返回。

**文档内容摘要:**
---
{text_summary}
---

**需要提取的信息:**
1.  文档标题 (document_title)
2.  文档编号 (document_id)
3.  版本信息 (version)
4.  编制日期 (create_date)
5.  编制人 (author)
6.  审核人 (reviewer)
7.  生效日期 (effective_date)

**请严格按照以下JSON格式返回，如果某项信息未在文本中找到，请将其值设为 null:**
```json
{{
  "document_title": "这里是文档的完整标题",
  "document_id": "这里是文档的唯一编号",
  "version": "这里是版本号",
  "create_date": "YYYY-MM-DD",
  "author": "这里是编制人的姓名",
  "reviewer": "这里是审核人的姓名",
  "effective_date": "YYYY-MM-DD"
}}
```
"""

    def get_route_analysis_prompt(self) -> str:
        """生成用于分析路线图的Prompt。"""
        return """
请仔细分析这张路线图/示意图，并关注以下关键要素：

1.  **管道标注**:
    *   是否有管道位置的清晰标注（通常用实线表示）？
    *   是否标注了管道中心线？
    *   是否有三条平行线（代表中心线及左右影响范围）？

2.  **影响范围**:
    *   是否用虚线圆圈等方式标注了潜在影响半径？
    *   影响范围的标注是否完整和清晰？

3.  **建筑物信息**:
    *   建筑物的位置和名称标注是否完整？
    *   是否标注了建筑物内的人员数量信息？
    *   建筑物的类型是否明确（如居民楼、学校、工厂）？

4.  **路线合理性**:
    *   疏散路线的方向是否正确（应背离管道向两侧疏散，而非沿管道方向）？
    *   进场路线是否清晰且适合救援车辆通行？
    *   路线是否穿越了不应穿越的区域（如建筑物、河流、山体）？

5.  **图例和标注**:
    *   是否有图例对图中的符号进行说明？
    *   所有文字标注是否清晰可读？
    *   是否标注了比例尺？

请以结构化的方式返回你的分析结果，包括发现的问题列表、合规的内容列表以及改进建议。
"""

    def get_signature_detection_prompt(self) -> str:
        """生成用于检测签名页的Prompt。"""
        return """
请仔细检查这张签名页或审批页，并报告以下信息：

1.  **签名识别**:
    *   识别所有手写签名的位置。
    *   评估每个签名的清晰度（清晰、模糊、无法识别）。
    *   统计有效签名的数量。

2.  **日期信息**:
    *   识别每个签名旁的手写日期。
    *   检查日期格式是否规范、是否清晰可读。
    *   验证签名的日期在逻辑上是否合理（例如，审批日期应晚于编制日期）。

3.  **表格与角色**:
    *   识别表格中定义的角色/职位（如编制、审核、批准）。
    *   检查是否有角色尚未签名（即空白签名位）。

4.  **印章识别**:
    *   检查页面上是否有公章或部门印章。
    *   描述印章的位置是否恰当（例如，是否覆盖了签名或关键信息）。

请详细描述你发现的签名信息和任何潜在的问题（如签名缺失、日期不清、逻辑错误等）。
"""

class ScoringPrompts:
    """
    封装了所有用于评分的Prompt模板。
    """

    def get_structure_completeness_prompt(self, sections_found: List[str], required_sections: List[str]) -> str:
        """生成用于评估结构完整性的Prompt。"""
        return f"""
请评估这份作业指导书的结构完整性，满分20分。

**评分标准:**
1. 必需章节覆盖（12分）：目录、职责、作业内容、相关文件、记录文件
2. 层级逻辑清晰（4分）：章节编号符合标准（如1.1.1分级）
3. 附录配套完整（4分）：附录与正文对应，无缺失关键附录

**文档实际包含的章节:**
{', '.join(sections_found)}

**必需章节列表:**
{', '.join(required_sections)}

**请严格按照以下JSON格式返回评分结果:**
```json
{{
  "score": 具体分数(0-20的整数),
  "reasoning": "详细评分理由",
  "missing_sections": ["缺失的章节1", "缺失的章节2"],
  "structure_issues": ["结构问题描述1", "结构问题描述2"],
  "suggestions": ["改进建议1", "改进建议2"]
}}
```
"""

    def get_content_completeness_prompt(self, content_summary: str, technical_info: dict = None) -> str:
        """生成用于评估内容完整性的Prompt。"""
        tech_info_str = str(technical_info) if technical_info else "无特定技术信息提取"
        
        return f"""
请评估这份作业指导书的内容完整性，满分40分。

**评分标准:**
1. 技术参数正确性（10分）：涉及的标准是否是最新标准，参数是否准确
2. 岗位职责完整性（10分）：是否包含对应的安全环保责任
3. 作业指引准确性（15分）：作业指引描述是否准确合理
4. 应急流程合理性（5分）：应急流程和应急处置卡是否合理

**文档内容摘要:**
{content_summary}

**提取的技术信息:**
{tech_info_str}

**请严格按照以下JSON格式返回评分结果:**
```json
{{
  "score": 具体分数(0-40的整数),
  "reasoning": "详细评分理由",
  "technical_issues": ["技术参数问题1", "技术参数问题2"],
  "responsibility_gaps": ["职责缺失1", "职责缺失2"],
  "procedure_issues": ["作业指引问题1", "作业指引问题2"],
  "emergency_issues": ["应急流程问题1", "应急流程问题2"],
  "suggestions": ["改进建议1", "改进建议2"]
}}
```
"""

    def get_grammar_errors_prompt(self, text_sample: str) -> str:
        """生成用于评估语法错误的Prompt。"""
        return f"""
请检查以下文档内容中的语法错误、错别字和表达问题，满分5分。

**评分标准:**
- 5分：无明显语法错误和错别字
- 4分：偶有轻微错误，不影响理解
- 3分：有一些错误，但整体可读
- 2分：错误较多，影响阅读体验
- 1分：错误很多，严重影响理解
- 0分：错误过多，难以理解

**文档内容样本:**
{text_sample}

**请严格按照以下JSON格式返回评分结果:**
```json
{{
  "score": 具体分数(0-5的整数),
  "reasoning": "详细评分理由",
  "grammar_errors": ["语法错误1", "语法错误2"],
  "typos": ["错别字1", "错别字2"],
  "expression_issues": ["表达问题1", "表达问题2"],
  "suggestions": ["改进建议1", "改进建议2"]
}}
```
"""

    def get_overall_scoring_prompt(self, document_summary: str, extracted_metadata: dict) -> str:
        """生成用于整体评分的Prompt。"""
        return f"""
请对这份作业指导书进行整体评估，满分100分。

**文档基本信息:**
- 标题: {extracted_metadata.get('document_title', '未知')}
- 编号: {extracted_metadata.get('document_id', '未知')}
- 版本: {extracted_metadata.get('version', '未知')}

**文档内容概要:**
{document_summary}

**请从以下几个维度进行评分:**
1. 结构完整性 (20分)
2. 内容完整性 (40分)
3. 语法规范性 (5分)
4. 引用可追溯性 (10分)
5. 业务逻辑性 (10分)
6. 人员配备 (5分)
7. 应急处置 (5分)
8. 处理效率 (5分)

**请严格按照以下JSON格式返回评分结果:**
```json
{{
  "total_score": 总分(0-100的整数),
  "detailed_scores": {{
    "structure_completeness": 具体分数,
    "content_completeness": 具体分数,
    "grammar_accuracy": 具体分数,
    "reference_traceability": 具体分数,
    "business_logic": 具体分数,
    "personnel_config": 具体分数,
    "emergency_procedures": 具体分数,
    "processing_efficiency": 具体分数
  }},
  "grade": "评级(优秀/良好/合格/不合格)",
  "main_issues": ["主要问题1", "主要问题2"],
  "suggestions": ["改进建议1", "改进建议2"],
  "reasoning": "综合评分理由"
}}
```
"""
