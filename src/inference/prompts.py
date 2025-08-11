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