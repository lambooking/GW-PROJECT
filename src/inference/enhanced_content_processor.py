"""
增强的内容摘要生成器，用于更智能地处理长文档。
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from ..data_processing.schemas import StandardizedDocument, TextContent

logger = logging.getLogger(__name__)

class EnhancedContentProcessor:
    """
    增强的内容处理器，用于更智能地从长文档中提取关键信息。
    """

    def __init__(self):
        # 重要章节的关键词
        self.important_keywords = [
            "职责", "作业内容", "作业流程", "操作步骤", "技术参数", 
            "安全要求", "应急处置", "风险", "质量", "标准", "规范",
            "编制", "审核", "批准", "生效", "版本", "修改"
        ]
        
        # 不同类型内容的权重
        self.content_weights = {
            "title": 1.0,      # 标题最重要
            "content": 0.8,    # 正文内容
            "table_caption": 0.9  # 表格标题也很重要
        }

    def generate_intelligent_summary(self, document: StandardizedDocument, 
                                   max_length: int = 2000, 
                                   include_all_titles: bool = True) -> str:
        """
        生成智能摘要，优先包含重要内容。
        
        Args:
            document: 标准化文档
            max_length: 最大字符数
            include_all_titles: 是否包含所有标题
            
        Returns:
            智能生成的摘要
        """
        logger.info(f"开始生成智能摘要，最大长度: {max_length}")
        
        # 1. 首先收集所有标题（章节结构）
        titles = []
        content_items = []
        
        for item in document.text_content:
            if item.section_type == "title":
                titles.append(item)
            else:
                content_items.append(item)
        
        # 2. 计算每个内容项的重要性得分
        scored_items = self._score_content_importance(content_items)
        
        # 3. 构建摘要
        summary_parts = []
        current_length = 0
        
        # 首先添加所有标题（如果启用）
        if include_all_titles:
            for title in titles:
                title_text = f"【{title.section_name}】"
                if current_length + len(title_text) <= max_length:
                    summary_parts.append(title_text)
                    current_length += len(title_text)
        
        # 然后按重要性添加内容
        for item, score in scored_items:
            if current_length >= max_length:
                break
                
            content = item.content
            available_space = max_length - current_length
            
            if len(content) > available_space:
                if available_space > 100:  # 至少保留100字符
                    content = content[:available_space-3] + "..."
                else:
                    break
            
            summary_parts.append(content)
            current_length += len(content)
        
        summary = "\n".join(summary_parts)
        logger.info(f"生成摘要完成，实际长度: {len(summary)} 字符")
        return summary

    def _score_content_importance(self, content_items: List[TextContent]) -> List[tuple]:
        """
        为内容项计算重要性得分。
        
        Returns:
            按得分排序的 (TextContent, score) 元组列表
        """
        scored_items = []
        
        for item in content_items:
            score = 0.0
            content = item.content.lower()
            
            # 基础权重
            score += self.content_weights.get(item.section_type, 0.5)
            
            # 关键词加分
            for keyword in self.important_keywords:
                if keyword in content:
                    score += 0.3
            
            # 长度加分（但不能过长）
            length_score = min(len(item.content) / 200, 1.0) * 0.2
            score += length_score
            
            # 页码加分（前面的内容更重要）
            if item.page_number <= 3:
                score += 0.5
            elif item.page_number <= 6:
                score += 0.3
            
            scored_items.append((item, score))
        
        # 按得分排序（降序）
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return scored_items

    def extract_section_structure(self, document: StandardizedDocument) -> Dict[str, Any]:
        """
        提取文档的章节结构。
        
        Returns:
            包含章节信息的字典
        """
        structure = {
            "total_sections": 0,
            "sections_by_level": {},
            "sections_found": [],
            "missing_sections": []
        }
        
        required_sections = ["目录", "范围", "职责", "作业内容", "相关文件", "记录文件"]
        found_sections = []
        
        for item in document.text_content:
            if item.section_type == "title" and item.section_name:
                structure["total_sections"] += 1
                found_sections.append(item.section_name)
                
                level = item.hierarchy_level or 0
                if level not in structure["sections_by_level"]:
                    structure["sections_by_level"][level] = []
                structure["sections_by_level"][level].append(item.section_name)
        
        structure["sections_found"] = found_sections
        
        # 检查缺失的必需章节
        for required in required_sections:
            if not any(required in found for found in found_sections):
                structure["missing_sections"].append(required)
        
        return structure

    def get_content_statistics(self, document: StandardizedDocument) -> Dict[str, Any]:
        """
        获取文档内容的统计信息。
        """
        stats = {
            "total_text_items": len(document.text_content),
            "total_tables": len(document.tables),
            "total_images": len(document.images),
            "total_pages": document.document_info.total_pages,
            "total_word_count": 0,
            "content_by_page": {},
            "content_types": {}
        }
        
        # 统计字数和内容分布
        for item in document.text_content:
            stats["total_word_count"] += item.word_count
            
            # 按页分组
            page = item.page_number
            if page not in stats["content_by_page"]:
                stats["content_by_page"][page] = {"items": 0, "words": 0}
            stats["content_by_page"][page]["items"] += 1
            stats["content_by_page"][page]["words"] += item.word_count
            
            # 按类型分组
            content_type = item.section_type
            if content_type not in stats["content_types"]:
                stats["content_types"][content_type] = {"count": 0, "words": 0}
            stats["content_types"][content_type]["count"] += 1
            stats["content_types"][content_type]["words"] += item.word_count
        
        return stats

    def extract_content_for_scoring_item(self, document: StandardizedDocument, scoring_item: str) -> str:
        """
        为特定的评分项提取专门的内容。
        
        Args:
            document: 标准化文档
            scoring_item: 评分项类型 (structure, content, grammar, metadata, safety, quality等)
            
        Returns:
            针对该评分项优化的内容字符串
        """
        if scoring_item == "structure":
            return self._extract_structure_content(document)
        elif scoring_item == "content":
            return self._extract_content_completeness_content(document)
        elif scoring_item == "grammar":
            return self._extract_grammar_sample_content(document)
        elif scoring_item == "metadata":
            return self._extract_metadata_content(document)
        elif scoring_item == "safety":
            return self._extract_safety_content(document)
        elif scoring_item == "quality":
            return self._extract_quality_content(document)
        elif scoring_item == "technical":
            return self._extract_technical_content(document)
        else:
            # 默认返回智能摘要
            return self.generate_intelligent_summary(document)

    def _extract_structure_content(self, document: StandardizedDocument) -> str:
        """提取用于结构完整性评分的内容：主要是目录和各级标题。"""
        content_parts = []
        
        # 1. 添加所有标题信息
        titles_by_level = {}
        for item in document.text_content:
            if item.section_type == "title" and item.section_name:
                level = item.hierarchy_level or 0
                if level not in titles_by_level:
                    titles_by_level[level] = []
                titles_by_level[level].append({
                    'name': item.section_name,
                    'page': item.page_number,
                    'content': item.content
                })
        
        content_parts.append("=== 文档章节结构 ===")
        for level in sorted(titles_by_level.keys()):
            content_parts.append(f"\n第{level}级标题:")
            for title_info in titles_by_level[level]:
                content_parts.append(f"  - {title_info['name']} (第{title_info['page']}页)")
        
        # 2. 添加目录相关内容
        content_parts.append("\n\n=== 目录内容 ===")
        for item in document.text_content:
            if "目录" in item.content or "contents" in item.content.lower():
                content_parts.append(f"第{item.page_number}页: {item.content}")
        
        # 3. 添加表格标题（表格也是结构的一部分）
        if document.tables:
            content_parts.append("\n\n=== 表格结构 ===")
            for table in document.tables:
                if table.caption:
                    content_parts.append(f"第{table.page_number}页: {table.caption}")
        
        return "\n".join(content_parts)

    def _extract_content_completeness_content(self, document: StandardizedDocument) -> str:
        """提取用于内容完整性评分的内容：重点关注作业内容、职责、技术参数等关键章节。"""
        important_keywords = [
            "职责", "作业内容", "作业流程", "操作步骤", "技术参数", 
            "作业条件", "工具材料", "质量要求", "注意事项"
        ]
        
        content_parts = []
        content_parts.append("=== 关键章节内容 ===")
        
        # 按关键词分类收集内容
        keyword_content = {keyword: [] for keyword in important_keywords}
        other_content = []
        
        for item in document.text_content:
            content_lower = item.content.lower()
            matched = False
            
            for keyword in important_keywords:
                if keyword in item.content:
                    keyword_content[keyword].append({
                        'page': item.page_number,
                        'content': item.content,
                        'type': item.section_type
                    })
                    matched = True
                    break
            
            if not matched and item.section_type in ['content', 'title']:
                other_content.append({
                    'page': item.page_number,
                    'content': item.content,
                    'type': item.section_type
                })
        
        # 输出关键词匹配的内容
        for keyword, items in keyword_content.items():
            if items:
                content_parts.append(f"\n--- {keyword}相关内容 ---")
                for item in items[:3]:  # 每个关键词最多3个条目
                    content_parts.append(f"第{item['page']}页: {item['content']}")
        
        # 添加其他重要内容（限制数量）
        content_parts.append("\n--- 其他重要内容 ---")
        for item in other_content[:5]:  # 最多5个其他条目
            content_parts.append(f"第{item['page']}页: {item['content']}")
        
        return "\n".join(content_parts)

    def _extract_grammar_sample_content(self, document: StandardizedDocument) -> str:
        """提取用于语法评估的内容：选择代表性的文本段落。"""
        content_parts = []
        content_parts.append("=== 语法评估文本样本 ===")
        
        # 选择不同页面的代表性段落
        samples_by_page = {}
        
        for item in document.text_content:
            if item.section_type == "content" and len(item.content) > 50:  # 只选择有意义的段落
                page = item.page_number
                if page not in samples_by_page:
                    samples_by_page[page] = []
                samples_by_page[page].append(item.content)
        
        # 每页选择1-2个段落，总共不超过10个段落
        sample_count = 0
        max_samples = 10
        
        for page in sorted(samples_by_page.keys()):
            if sample_count >= max_samples:
                break
            content_parts.append(f"\n--- 第{page}页样本 ---")
            for content in samples_by_page[page][:2]:  # 每页最多2个段落
                if sample_count >= max_samples:
                    break
                content_parts.append(content)
                sample_count += 1
        
        return "\n".join(content_parts)

    def _extract_metadata_content(self, document: StandardizedDocument) -> str:
        """提取用于元数据提取的内容：重点关注文档标题、编号、版本等信息。"""
        content_parts = []
        content_parts.append("=== 文档元数据相关内容 ===")
        
        # 前3页的所有内容（元数据通常在前面）
        for item in document.text_content:
            if item.page_number <= 3:
                content_parts.append(f"第{item.page_number}页 [{item.section_type}]: {item.content}")
        
        # 查找可能包含版本、日期等信息的后续内容
        metadata_keywords = ["版本", "编制", "审核", "批准", "生效", "修改", "编号"]
        content_parts.append("\n--- 版本控制信息 ---")
        
        for item in document.text_content:
            if item.page_number > 3:  # 避免重复
                for keyword in metadata_keywords:
                    if keyword in item.content:
                        content_parts.append(f"第{item.page_number}页: {item.content}")
                        break
        
        return "\n".join(content_parts)

    def _extract_safety_content(self, document: StandardizedDocument) -> str:
        """提取安全相关内容。"""
        safety_keywords = ["安全", "风险", "危险", "防护", "应急", "事故", "防范"]
        return self._extract_keyword_content(document, safety_keywords, "安全要求")

    def _extract_quality_content(self, document: StandardizedDocument) -> str:
        """提取质量相关内容。"""
        quality_keywords = ["质量", "标准", "规范", "要求", "检查", "验收", "合格"]
        return self._extract_keyword_content(document, quality_keywords, "质量标准")

    def _extract_technical_content(self, document: StandardizedDocument) -> str:
        """提取技术参数相关内容。"""
        technical_keywords = ["参数", "规格", "技术", "性能", "指标", "数据"]
        return self._extract_keyword_content(document, technical_keywords, "技术参数")

    def _extract_keyword_content(self, document: StandardizedDocument, keywords: List[str], category: str) -> str:
        """根据关键词提取特定类别的内容。"""
        content_parts = []
        content_parts.append(f"=== {category}相关内容 ===")
        
        matched_items = []
        for item in document.text_content:
            for keyword in keywords:
                if keyword in item.content:
                    matched_items.append({
                        'page': item.page_number,
                        'content': item.content,
                        'keyword': keyword
                    })
                    break
        
        # 去重并限制数量
        seen_content = set()
        for item in matched_items[:10]:  # 最多10个条目
            if item['content'] not in seen_content:
                content_parts.append(f"第{item['page']}页 [关键词:{item['keyword']}]: {item['content']}")
                seen_content.add(item['content'])
        
        if not matched_items:
            content_parts.append(f"未找到{category}相关内容")
        
        return "\n".join(content_parts)

    def extract_and_save_all_scoring_contents(self, document: StandardizedDocument, 
                                            output_dir: Path = None) -> Dict[str, Any]:
        """
        提取所有评分项的专门内容并保存为结构化JSON。
        
        Args:
            document: 标准化文档
            output_dir: 输出目录，默认为 output/extracted_contents/
            
        Returns:
            包含所有提取内容的结构化字典
        """
        logger.info("🔄 开始提取所有评分项的专门内容...")
        
        # 设置默认输出目录
        if output_dir is None:
            output_dir = Path(__file__).parent.parent.parent / "output" / "extracted_contents"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extracted_contents_{document.document_info.file_name}_{timestamp}.json"
        output_file = output_dir / filename
        
        # 提取所有类型的内容
        scoring_items = {
            "structure": "结构完整性",
            "content": "内容完整性", 
            "grammar": "语法规范性",
            "metadata": "元数据提取",
            "safety": "安全相关",
            "quality": "质量相关",
            "technical": "技术参数"
        }
        
        extracted_data = {
            "document_info": {
                "file_name": document.document_info.file_name,
                "scene_type": document.document_info.scene_type,
                "scene_name": document.document_info.scene_name,
                "total_pages": document.document_info.total_pages,
                "processing_timestamp": document.document_info.processing_timestamp.isoformat(),
                "classification_confidence": document.document_info.classification_confidence
            },
            "extraction_info": {
                "extraction_timestamp": datetime.now().isoformat(),
                "processor_version": "enhanced_v1.0",
                "total_scoring_items": len(scoring_items)
            },
            "document_statistics": self.get_content_statistics(document),
            "section_structure": self.extract_section_structure(document),
            "scoring_contents": {},
            "raw_content_summary": {
                "total_text_items": len(document.text_content),
                "total_tables": len(document.tables),
                "total_images": len(document.images)
            }
        }
        
        # 提取每个评分项的专门内容
        for item_type, item_name in scoring_items.items():
            logger.info(f"正在提取 {item_name} 相关内容...")
            
            try:
                content = self.extract_content_for_scoring_item(document, item_type)
                
                # 分析内容统计
                content_stats = self._analyze_extracted_content(content, item_type)
                
                extracted_data["scoring_contents"][item_type] = {
                    "name": item_name,
                    "content": content,
                    "statistics": content_stats,
                    "extraction_success": True
                }
                
                logger.info(f"✅ {item_name} 内容提取完成，长度: {len(content)} 字符")
                
            except Exception as e:
                logger.error(f"❌ {item_name} 内容提取失败: {e}")
                extracted_data["scoring_contents"][item_type] = {
                    "name": item_name,
                    "content": "",
                    "error": str(e),
                    "extraction_success": False
                }
        
        # 保存到JSON文件
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 提取内容已保存到: {output_file}")
            
            # 打印摘要
            self._print_extraction_summary(extracted_data, output_file)
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"❌ 保存提取内容失败: {e}")
            return extracted_data

    def _analyze_extracted_content(self, content: str, content_type: str) -> Dict[str, Any]:
        """
        分析提取内容的统计信息。
        """
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # 提取页码信息
        page_mentions = []
        for line in lines:
            if "第" in line and "页" in line:
                try:
                    import re
                    page_matches = re.findall(r'第(\d+)页', line)
                    page_mentions.extend([int(p) for p in page_matches])
                except:
                    pass
        
        unique_pages = sorted(set(page_mentions)) if page_mentions else []
        
        # 分析内容类型
        section_headers = len([line for line in lines if line.startswith("===")])
        content_blocks = len([line for line in lines if line.startswith("---")])
        
        return {
            "total_length": len(content),
            "total_lines": len(lines),
            "non_empty_lines": len(non_empty_lines),
            "pages_covered": unique_pages,
            "page_count": len(unique_pages),
            "section_headers": section_headers,
            "content_blocks": content_blocks,
            "avg_line_length": sum(len(line) for line in non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0
        }

    def _print_extraction_summary(self, extracted_data: Dict[str, Any], output_file: Path):
        """
        打印提取内容的完整摘要。
        """
        print("\n" + "=" * 80)
        print("📊 分项内容提取完整报告")
        print("=" * 80)
        
        doc_info = extracted_data["document_info"]
        print(f"📄 文档名称: {doc_info['file_name']}")
        print(f"📋 场景类型: {doc_info['scene_type']} ({doc_info['scene_name']})")
        print(f"📊 总页数: {doc_info['total_pages']}")
        print(f"🕒 处理时间: {doc_info['processing_timestamp']}")
        
        stats = extracted_data["document_statistics"]
        print(f"\n📈 文档统计:")
        print(f"  - 文本段落: {stats['total_text_items']}")
        print(f"  - 表格数量: {stats['total_tables']}")
        print(f"  - 图片数量: {stats['total_images']}")
        print(f"  - 总字数: {stats['total_word_count']}")
        
        structure = extracted_data["section_structure"]
        print(f"\n🏗️ 章节结构:")
        print(f"  - 总章节数: {structure['total_sections']}")
        print(f"  - 发现章节: {', '.join(structure['sections_found'])}")
        if structure['missing_sections']:
            print(f"  - 缺失章节: {', '.join(structure['missing_sections'])}")
        
        print(f"\n🎯 各评分项提取结果:")
        scoring_contents = extracted_data["scoring_contents"]
        
        for item_type, item_data in scoring_contents.items():
            status = "✅" if item_data["extraction_success"] else "❌"
            print(f"\n{status} {item_data['name']} ({item_type}):")
            
            if item_data["extraction_success"]:
                stats = item_data["statistics"]
                print(f"    📏 内容长度: {stats['total_length']} 字符")
                print(f"    📄 覆盖页面: {stats['page_count']} 页 {stats['pages_covered']}")
                print(f"    📝 有效行数: {stats['non_empty_lines']}")
                print(f"    🗂️ 内容块数: {stats['content_blocks']}")
                
                # 显示内容预览
                content_preview = item_data["content"][:200]
                if len(item_data["content"]) > 200:
                    content_preview += "..."
                print(f"    👀 内容预览: {content_preview}")
            else:
                print(f"    ❌ 提取失败: {item_data.get('error', '未知错误')}")
        
        print(f"\n💾 完整数据已保存到: {output_file}")
        print(f"📁 文件大小: {output_file.stat().st_size / 1024:.1f} KB")
        
        print("\n" + "=" * 80)
        print("✅ 分项内容提取完成")
        print("=" * 80)