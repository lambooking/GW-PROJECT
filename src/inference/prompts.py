"""
优化后的评分Prompt系统：简洁、直接、高效
采用结构化输出格式，确保LLM返回可解析的结果
"""

class ScoringPrompts:
    """
    优化后的评分Prompt系统：简洁、聚焦、高效
    """
    
    def get_structure_completeness_prompt(self, context: str, required_sections: list) -> str:
        """
        结构完整性评分 - 简化版prompt
        """
        sections_str = ", ".join(required_sections)
        
        prompt = f"""
分析文档是否包含必需章节：{sections_str}

文档内容：
{context}

请按以下格式回答：

分数：X/20
找到章节：[列出找到的章节]
缺失章节：[列出缺失的章节，如无则写"无"]
评价：[简要说明结构完整性情况]
"""
        return prompt

    def get_content_completeness_prompt(self, context: str, max_score: int = 30) -> str:
        """
        内容完整性评分 - 简化版prompt
        """
        prompt = f"""
评估作业指导书内容完整性（满分{max_score}分）：

内容：
{context}

评分标准：
- 操作步骤是否详细具体 ({max_score//3}分)
- 内容是否可操作实用 ({max_score//3}分) 
- 关键环节覆盖度 ({max_score//3}分)

请按以下格式回答：

分数：X/{max_score}
理由：[详细说明内容完整性的优缺点]
"""
        return prompt

    def get_grammar_errors_prompt(self, context: str, max_score: int = 10) -> str:
        """
        语法规范性评分 - 简化版prompt
        """
        prompt = f"""
检查文档语法规范性（满分{max_score}分）：

文档内容：
{context}

检查要点：
- 语法错误、错别字
- 表达是否通顺清晰
- 专业术语使用规范性

请按以下格式回答：

分数：X/{max_score}
问题：[指出发现的主要语法/表达问题，如无则写"无明显问题"]
评价：[整体语言质量评价]
"""
        return prompt

    def get_technical_accuracy_prompt(self, context: str, max_score: int = 25) -> str:
        """
        技术准确性评分prompt
        """
        prompt = f"""
评估技术内容准确性（满分{max_score}分）：

技术内容：
{context}

评分要点：
- 技术参数是否准确 (7分)
- 专业术语是否规范 (6分) 
- 技术要求可执行性 (7分)
- 行业标准符合性 (5分)

请按以下格式回答：

分数：X/{max_score}
理由：[分别评价技术参数、专业术语、可执行性、标准符合性]
"""
        return prompt
    
    def get_safety_compliance_prompt(self, context: str, max_score: int = 15) -> str:
        """
        安全合规性评分prompt  
        """
        prompt = f"""
评估安全合规性（满分{max_score}分）：

安全内容：
{context}

评分要点：
- 安全风险识别 (4分)
- 防护措施完整性 (4分)
- 应急处置流程 (4分)
- 安全责任明确性 (3分)

请按以下格式回答：

分数：X/{max_score}
理由：[分别评价风险识别、防护措施、应急流程、责任划分]
"""
        return prompt

    # === 场景二（多模态）相关 Prompt ===
    def get_route_map_evaluation_prompt(self, context: str, max_score: int = 20) -> str:
        """
        评估入场/疏散路线图的完整性与清晰度（多模态）
        要求输出：分数与理由
        """
        prompt = f"""
你将看到一张或多张与现场路线相关的图片（如入场线路、疏散/逃生路线、集合点等），并给你部分文本上下文。
请结合图片与文本，对“路线信息完整性与清晰度”进行打分（满分{max_score}分）。

文本上下文：
{context}

评估要点：
- 路线是否标注清晰（起点、关键节点、终点、方向箭头、备用路线）
- 是否包含集合点/疏散点、危险区域标注
- 图例/标识是否明确，是否便于执行

请严格按以下格式输出：

分数：X/{max_score}
理由：[简要说明图中标注、清晰度、可执行性]
"""
        return prompt

    def get_signature_verification_prompt(self, context: str, max_score: int = 15) -> str:
        """
        评估签字/盖章页的完整性（多模态）
        """
        prompt = f"""
你将看到一张或多张包含签字/签章/审核批注的页面图像，并有部分文本上下文。
请判断签字页是否完整、清晰，角色是否齐全（编制、审核、批准等），并对"签字盖章完整性"打分（满分{max_score}分）。

文本上下文：
{context}

请严格按以下格式输出：

分数：X/{max_score}
理由：[签字角色是否齐全、签章是否清晰、日期是否可辨识]
"""
        return prompt
    
    def get_signature_verification_with_details_prompt(self, context: str, max_score: int = 15) -> str:
        """
        评估签字/盖章页完整性并提取结构化信息（多模态）
        """
        prompt = f"""
你将看到多张图片（通常是文档的封面和前几页）。

**第一步：逐张分析每张图片**
- 图片1：查找是否有签字栏/表格，标注了哪些角色？
- 图片2：查找是否有签字栏/表格，标注了哪些角色？
- 图片3：查找是否有签字栏/表格，标注了哪些角色？
- 后续图片：继续查找

**第二步：识别以下角色的信息**
需要找到这些角色（注意：有些文档用不同名称）：
1. 编制（可能写作：编制、起草、编写、拟稿人）
2. 校对（可能写作：校对、校核）
3. 审核（可能写作：审核、复核、审查）
4. 批准（可能写作：批准、签发、批准人、核准人）

**第三步：提取姓名和日期**
- 姓名：通常是手写的2-4个中文字符
- 日期：格式如 2024年7月24日、2024-7-24、2024.7.24

**关键提示**：
✓ 表格里的签字栏通常包含：编制、校对、审核（在同一张图/表格中）
✓ 批准人签字可能在单独的页面
✓ 即使字迹潦草也要尽力识别，看清楚每个角色栏位
✓ 注意区分"签字"和"盖章"（红色印章）

**输出格式**（严格按此格式）：

图片分析：
- 图1：[描述看到了什么]
- 图2：[描述看到了什么，特别是表格签字栏]
- 图3：[描述看到了什么]

提取结果：
编制：[姓名]，[日期]
校对：[姓名]，[日期]
审核：[姓名]，[日期]
批准：[姓名]，[日期]

分数：X/{max_score}
评价：[综合评价]

**示例**：
图片分析：
- 图1：封面页，包含文档标题
- 图2：签字审批页，有表格包含编制、校对、审核三栏，有手写签名
- 图3：批准页，右下角有批准人签字和日期

提取结果：
编制：张三，2024年7月20日
校对：李四，无
审核：王五，2024年7月21日
批准：赵六，2024年8月1日

分数：14/{max_score}
评价：签字栏完整，所有角色均有签字，日期清晰可辨，时序合理。

文本参考：{context[:300]}
"""
        return prompt

    def get_hca_image_analysis_prompt(self, context: str, max_score: int = 25) -> str:
        """
        评估高后果区（HCA）影像/示意图是否覆盖关键区域、风险点标注是否充分（多模态）
        """
        prompt = f"""
你将看到与高后果区（HCA）相关的图片（影像图/示意图），并得到部分文本上下文。
请评估“关键区域覆盖与风险标注充分性”（满分{max_score}分）。

文本上下文：
{context}

评估要点：
- 关键敏感区域（人员密集、环境敏感、重要设施）是否清晰标明
- 潜在影响半径/边界是否直观可识别
- 风险点与相应管控信息是否明确

请严格按以下格式输出：

分数：X/{max_score}
理由：[覆盖范围与标注充分性的判断]
"""
        return prompt

    def get_risk_controls_visual_prompt(self, context: str, max_score: int = 25) -> str:
        """
        评估现场风险提示与管控标识的可见性与规范性（多模态）
        """
        prompt = f"""
你将看到与现场照片/示意有关的图片，并得到部分文本上下文。
请评估“现场风险提示与管控标识的可见性与规范性”（满分{max_score}分）。

文本上下文：
{context}

评估要点：
- 警示标识是否规范、清晰可见
- 物理隔离/围挡/防护是否到位
- 临时施工/作业区风险告知是否充分

请严格按以下格式输出：

分数：X/{max_score}
理由：[标识与防护是否充分、规范]
"""
        return prompt

    def get_emergency_evac_plan_prompt(self, context: str, max_score: int = 15) -> str:
        """
        评估应急疏散方案的图文一致性与可操作性（多模态）
        """
        prompt = f"""
你将看到与应急疏散/集合点/通道相关的图片，并得到部分文本上下文。
请评估“应急疏散方案的图文一致性与可操作性”（满分{max_score}分）。

文本上下文：
{context}

评估要点：
- 集合点、疏散通道是否清晰，是否与文本描述一致
- 方向、距离、障碍物等关键信息是否明确

请严格按以下格式输出：

分数：X/{max_score}
理由：[图文一致性与可操作性的判断]
"""
        return prompt
        
    def parse_simple_response(self, response: str, max_score: int) -> tuple[int, str]:
        """
        解析简化格式的LLM响应
        """
        import re
        
        score = 0
        reasoning = response.strip()
        
        # 查找"分数：X/Y"格式
        score_match = re.search(r'分数[：:]\s*(\d+)\s*/\s*\d+', response)
        if score_match:
            score = min(int(score_match.group(1)), max_score)
        else:
            # 备用：查找任何"X分"格式
            score_match = re.search(r'(\d+)\s*分', response)
            if score_match:
                score = min(int(score_match.group(1)), max_score)
        
        return score, reasoning

class ExtractionPrompts:
    """
    信息提取相关的Prompt集合。
    目前用于从文档中抽取基础元数据（标题、编号、版本、日期、编制单位等）。
    """

    def get_metadata_prompt(self, context: str) -> str:
        """
        生成元数据提取的Prompt，请模型以JSON格式输出可解析结果。
        """
        prompt = f"""
你是一个严谨的文档信息抽取助手。请从以下内容中提取基础元数据，并严格输出JSON：

文档内容：
{context}

请输出如下JSON对象（不存在则置为null或空字符串）：
{{
  "title": string | null,
  "document_number": string | null,
  "version": string | null,
  "date": string | null,            # 格式优先 YYYY-MM-DD
  "department": string | null,
  "author": string | null,
  "reviewer": string | null,
  "approver": string | null,
  "keywords": [string]
}}

只输出JSON，不要附加解释。
"""
        return prompt