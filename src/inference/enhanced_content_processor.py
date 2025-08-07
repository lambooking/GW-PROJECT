"""
增强的内容处理器，针对不同评分项提取专门的内容。
"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set

from ..data_processing.schemas import StandardizedDocument, TextContent

logger = logging.getLogger(__name__)

class EnhancedContentProcessor:
    """
    增强的内容处理器，为每个评分项提取专门的内容。
    这样可以避免内容长度限制，并提高评分的针对性。
    """

    def __init__(self, output_dir: str = "output/extracted_contents"):
        """
        初始化内容处理器。

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 评分项定义
        self.scoring_items = {
            "metadata": {
                "name": "元数据提取",
                "keywords": ["版本", "编号", "编制", "审核", "批准", "日期", "作者", "修改"],
                "pages": [1, 2, 11, 12],  # 通常在首页、最后几页
                "extract_method": "metadata_focused"
            },
            "structure": {
                "name": "结构完整性", 
                "keywords": ["目录", "章节", "编号", "附录", "条款"],
                "pages": "all",
                "extract_method": "structure_focused"
            },
            "content": {
                "name": "内容完整性",
                "keywords": ["职责", "作业内容", "操作", "流程", "步骤", "要求"],
                "pages": [1, 2, 3, 4, 5],  # 主要内容页
                "extract_method": "content_focused"
            },
            "grammar": {
                "name": "语法规范性",
                "keywords": [],
                "pages": [1, 2, 3],  # 前几页样本
                "extract_method": "grammar_focused"
            },
            "safety": {
                "name": "安全相关",
                "keywords": ["安全", "风险", "应急", "防护", "危险", "事故", "预警"],
                "pages": "all",
                "extract_method": "keyword_focused"
            },
            "quality": {
                "name": "质量相关", 
                "keywords": ["质量", "标准", "规范", "要求", "检查", "验收", "合格"],
                "pages": "all",
                "extract_method": "keyword_focused"
            },
            "technical": {
                "name": "技术参数",
                "keywords": ["参数", "指标", "标准", "规格", "技术", "数据", "测量"],
                "pages": "all",
                "extract_method": "keyword_focused"
            }
        }

    def extract_all_contents(self, document: StandardizedDocument) -> Dict[str, Any]:
        """
        为所有评分项提取专门的内容。

        Args:
            document: 标准化文档对象

        Returns:
            包含所有提取内容的字典
        """
        logger.info(f"开始为文档 '{document.document_info.file_name}' 提取分项内容...")
        
        # 分析文档统计信息
        doc_stats = self._analyze_document_statistics(document)
        
        # 分析章节结构
        section_structure = self._analyze_section_structure(document)
        
        # 为每个评分项提取内容
        scoring_contents = {}
        for item_key, item_config in self.scoring_items.items():
            logger.info(f"正在提取 {item_config['name']} 的内容...")
            
            try:
                content_data = self._extract_content_for_item(
                    document, item_key, item_config
                )
                scoring_contents[item_key] = content_data
                logger.info(f"✓ {item_config['name']} 内容提取成功，长度: {len(content_data['content'])} 字符")
                
            except Exception as e:
                logger.error(f"✗ {item_config['name']} 内容提取失败: {e}")
                scoring_contents[item_key] = {
                    "name": item_config['name'],
                    "content": "",
                    "statistics": {},
                    "extraction_success": False,
                    "error": str(e)
                }

        # 组装完整结果
        result = {
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
                "processor_version": "enhanced_v2.0",
                "total_scoring_items": len(self.scoring_items)
            },
            "document_statistics": doc_stats,
            "section_structure": section_structure,
            "scoring_contents": scoring_contents,
            "raw_content_summary": {
                "total_text_items": len(document.text_content),
                "total_tables": len(document.tables),
                "total_images": len(document.images)
            }
        }

        # 保存到文件
        self._save_to_file(result, document.document_info.file_name)
        
        logger.info(f"文档 '{document.document_info.file_name}' 的所有内容提取完成！")
        return result

    def _extract_content_for_item(self, document: StandardizedDocument, 
                                 item_key: str, item_config: Dict[str, Any]) -> Dict[str, Any]:
        """为特定评分项提取内容"""
        
        method = item_config.get("extract_method", "keyword_focused")
        
        if method == "metadata_focused":
            return self._extract_metadata_content(document, item_config)
        elif method == "structure_focused":
            return self._extract_structure_content(document, item_config)
        elif method == "content_focused":
            return self._extract_main_content(document, item_config)
        elif method == "grammar_focused":
            return self._extract_grammar_sample(document, item_config)
        elif method == "keyword_focused":
            return self._extract_keyword_content(document, item_config)
        else:
            return self._extract_general_content(document, item_config)

    def _extract_metadata_content(self, document: StandardizedDocument, 
                                 item_config: Dict[str, Any]) -> Dict[str, Any]:
        """提取元数据相关内容"""
        content_parts = []
        statistics = {"pages_covered": [], "total_length": 0}
        
        # 重点关注首页和尾页
        target_pages = item_config.get("pages", [1, 2, 11, 12])
        
        # 首先提取版本控制信息（通常在每页顶部）
        version_info = []
        for text_item in document.text_content[:10]:  # 前10项通常包含版本信息
            content = text_item.content
            if any(keyword in content for keyword in ["发行版本", "修改码", "文件编码", "页码"]):
                version_info.append(f"版本控制信息: {content}")
        
        if version_info:
            # 版本控制信息
            content_parts.extend(version_info)
            content_parts.append("")

        # 提取目标页面的详细内容
        # 文档元数据相关内容
        for text_item in document.text_content:
            if text_item.page_number in target_pages:
                # 标注页面和内容类型
                content_type = text_item.section_type or "content"
                page_info = text_item.content
                content_parts.append(page_info)
                
                if text_item.page_number not in statistics["pages_covered"]:
                    statistics["pages_covered"].append(text_item.page_number)

        # 查找签名页信息
        signature_content = []
        for text_item in document.text_content:
            content = text_item.content
            if any(keyword in content for keyword in ["编写", "审核", "批准", "签名", "日期"]):
                signature_content.append(content)
        
        if signature_content:
            content_parts.append("")
            # 签名和审批信息
            content_parts.extend(signature_content)

        final_content = "\n".join(content_parts)
        statistics.update({
            "total_length": len(final_content),
            "total_lines": len(content_parts),
            "non_empty_lines": len([line for line in content_parts if line.strip()]),
            "page_count": len(statistics["pages_covered"]),
            "version_info_found": len(version_info),
            "signature_info_found": len(signature_content)
        })

        return {
            "name": item_config["name"],
            "content": final_content,
            "statistics": statistics,
            "extraction_success": True
        }

    def _extract_structure_content(self, document: StandardizedDocument, 
                                  item_config: Dict[str, Any]) -> Dict[str, Any]:
        """提取结构相关内容"""
        content_parts = []
        statistics = {"pages_covered": set(), "total_length": 0}

        # 提取章节结构
        # 文档章节结构
        content_parts.append("")
        
        # 按层级组织章节
        sections_by_level = {}
        for text_item in document.text_content:
            if text_item.section_type == "title" and text_item.section_name:
                level = text_item.hierarchy_level or 1
                if level not in sections_by_level:
                    sections_by_level[level] = []
                sections_by_level[level].append(f"  - {text_item.section_name}")
                statistics["pages_covered"].add(text_item.page_number)

        for level in sorted(sections_by_level.keys()):
            content_parts.append(f"第{level}级标题:")
            content_parts.extend(sections_by_level[level])
            content_parts.append("")

        # 查找目录内容
        # 目录内容
        for text_item in document.text_content:
            if any(keyword in text_item.content.lower() for keyword in ["目录", "contents", "索引"]):
                content_parts.append(f"{text_item.content}")
                statistics["pages_covered"].add(text_item.page_number)
        content_parts.append("")

        # 提取表格结构信息
        # 表格结构
        for i, table in enumerate(document.tables):
            if table.caption:
                content_parts.append(f"表格{i+1}: {table.caption}")
            else:
                content_parts.append(f"表格{i+1}: {len(table.headers)}列 x {len(table.data)}行")
            if table.headers:
                content_parts.append(f"  表头: {', '.join(table.headers[:5])}{'...' if len(table.headers) > 5 else ''}")
            statistics["pages_covered"].add(table.page_number)

        final_content = "\n".join(content_parts)
        statistics.update({
            "total_length": len(final_content),
            "total_lines": len(content_parts),
            "non_empty_lines": len([line for line in content_parts if line.strip()]),
            "pages_covered": sorted(list(statistics["pages_covered"])),
            "page_count": len(statistics["pages_covered"]),
            "section_headers": sum(len(sections) for sections in sections_by_level.values()),
            "tables_found": len(document.tables),
            "avg_line_length": len(final_content) / len(content_parts) if content_parts else 0
        })

        return {
            "name": item_config["name"],
            "content": final_content,
            "statistics": statistics,
            "extraction_success": True
        }

    def _extract_main_content(self, document: StandardizedDocument, 
                             item_config: Dict[str, Any]) -> Dict[str, Any]:
        """提取主要内容"""
        content_parts = []
        statistics = {"pages_covered": set(), "total_length": 0}
        keywords = item_config.get("keywords", [])
        target_pages = item_config.get("pages", [1, 2, 3, 4, 5])

        # 关键章节内容
        content_parts.append("")

        # 按关键词分类提取内容
        keyword_sections = {}
        for keyword in keywords:
            keyword_sections[keyword] = []

        # 其他重要内容
        other_content = []

        for text_item in document.text_content:
            if text_item.page_number not in target_pages:
                continue
                
            content = text_item.content
            found_keyword = False
            
            # 检查是否包含关键词
            for keyword in keywords:
                if keyword in content:
                    keyword_sections[keyword].append(content)
                    found_keyword = True
                    break
            
            # 如果没有匹配关键词，但是重要内容（如标题或长段落），也保留
            if not found_keyword and (text_item.section_type == "title" or len(content) > 50):
                other_content.append(content)
            
            statistics["pages_covered"].add(text_item.page_number)

        # 组织输出
        for keyword in keywords:
            if keyword_sections[keyword]:
                content_parts.append(f"--- {keyword}相关内容 ---")
                content_parts.extend(keyword_sections[keyword][:3])  # 限制每个关键词最多3个条目
                content_parts.append("")

        if other_content:
            content_parts.append("--- 其他重要内容 ---")
            content_parts.extend(other_content[:5])  # 限制其他内容最多5个条目

        final_content = "\n".join(content_parts)
        statistics.update({
            "total_length": len(final_content),
            "total_lines": len(content_parts),
            "non_empty_lines": len([line for line in content_parts if line.strip()]),
            "pages_covered": sorted(list(statistics["pages_covered"])),
            "page_count": len(statistics["pages_covered"]),
            "keyword_matches": sum(len(sections) for sections in keyword_sections.values()),
            "other_content_items": len(other_content),
            "avg_line_length": len(final_content) / len(content_parts) if content_parts else 0
        })

        return {
            "name": item_config["name"],
            "content": final_content,
            "statistics": statistics,
            "extraction_success": True
        }

    def _extract_grammar_sample(self, document: StandardizedDocument, 
                               item_config: Dict[str, Any]) -> Dict[str, Any]:
        """提取语法评估样本"""
        content_parts = []
        statistics = {"pages_covered": set(), "total_length": 0}
        target_pages = item_config.get("pages", [1, 2, 3])

        # 语法评估文本样本
        content_parts.append("")

        # 每页选择代表性段落
        for page_num in target_pages:
            page_content = []
            for text_item in document.text_content:
                if text_item.page_number == page_num and len(text_item.content) > 20:
                    page_content.append(text_item.content)
            
            if page_content:
                content_parts.append(f"--- 第{page_num}页样本 ---")
                # 选择前3个段落作为样本
                for i, content in enumerate(page_content[:3]):
                    content_parts.append(content)
                    if i < len(page_content[:3]) - 1:
                        content_parts.append("")
                content_parts.append("")
                statistics["pages_covered"].add(page_num)

        final_content = "\n".join(content_parts)
        statistics.update({
            "total_length": len(final_content),
            "total_lines": len(content_parts),
            "non_empty_lines": len([line for line in content_parts if line.strip()]),
            "pages_covered": sorted(list(statistics["pages_covered"])),
            "page_count": len(statistics["pages_covered"]),
            "sample_paragraphs": len([line for line in content_parts if line and not line.startswith("---") and not line.startswith("===")]),
            "avg_line_length": len(final_content) / len(content_parts) if content_parts else 0
        })

        return {
            "name": item_config["name"],
            "content": final_content,
            "statistics": statistics,
            "extraction_success": True
        }

    def _extract_keyword_content(self, document: StandardizedDocument, 
                                item_config: Dict[str, Any]) -> Dict[str, Any]:
        """基于关键词提取内容"""
        content_parts = []
        statistics = {"pages_covered": set(), "total_length": 0}
        keywords = item_config.get("keywords", [])

        # {item_config['name']}相关内容
        content_parts.append("")

        # 按关键词搜索相关内容
        for text_item in document.text_content:
            content = text_item.content
            for keyword in keywords:
                if keyword in content:
                    content_parts.append(content)
                    statistics["pages_covered"].add(text_item.page_number)
                    break  # 避免同一段落多次添加

        final_content = "\n".join(content_parts)
        statistics.update({
            "total_length": len(final_content),
            "total_lines": len(content_parts),
            "non_empty_lines": len([line for line in content_parts if line.strip()]),
            "pages_covered": sorted(list(statistics["pages_covered"])),
            "page_count": len(statistics["pages_covered"]),
            "keyword_matches": len([line for line in content_parts if "[关键词:" in line]),
            "avg_line_length": len(final_content) / len(content_parts) if content_parts else 0
        })

        return {
            "name": item_config["name"],
            "content": final_content,
            "statistics": statistics,
            "extraction_success": True
        }

    def _extract_general_content(self, document: StandardizedDocument, 
                                item_config: Dict[str, Any]) -> Dict[str, Any]:
        """通用内容提取方法"""
        content_parts = []
        statistics = {"pages_covered": set(), "total_length": 0}
        
        # 简单地提取前几页的内容
        for text_item in document.text_content[:10]:
            content_parts.append(text_item.content)
            statistics["pages_covered"].add(text_item.page_number)

        final_content = "\n".join(content_parts)
        statistics.update({
            "total_length": len(final_content),
            "total_lines": len(content_parts),
            "pages_covered": sorted(list(statistics["pages_covered"])),
            "page_count": len(statistics["pages_covered"])
        })

        return {
            "name": item_config["name"],
            "content": final_content,
            "statistics": statistics,
            "extraction_success": True
        }

    def _analyze_document_statistics(self, document: StandardizedDocument) -> Dict[str, Any]:
        """分析文档统计信息"""
        stats = {
            "total_text_items": len(document.text_content),
            "total_tables": len(document.tables),
            "total_images": len(document.images),
            "total_pages": document.document_info.total_pages,
            "total_word_count": sum(text.word_count for text in document.text_content),
            "content_by_page": {},
            "content_types": {}
        }

        # 按页面统计
        page_stats = {}
        for text_item in document.text_content:
            page_num = text_item.page_number
            if page_num not in page_stats:
                page_stats[page_num] = {"items": 0, "words": 0}
            page_stats[page_num]["items"] += 1
            page_stats[page_num]["words"] += text_item.word_count

        stats["content_by_page"] = {str(k): v for k, v in sorted(page_stats.items())}

        # 按内容类型统计
        type_stats = {}
        for text_item in document.text_content:
            content_type = text_item.section_type or "content"
            if content_type not in type_stats:
                type_stats[content_type] = {"count": 0, "words": 0}
            type_stats[content_type]["count"] += 1
            type_stats[content_type]["words"] += text_item.word_count

        stats["content_types"] = type_stats
        return stats

    def _analyze_section_structure(self, document: StandardizedDocument) -> Dict[str, Any]:
        """分析章节结构"""
        sections = []
        sections_by_level = {}
        
        for text_item in document.text_content:
            if text_item.section_type == "title" and text_item.section_name:
                sections.append(text_item.section_name)
                level = text_item.hierarchy_level or 1
                if level not in sections_by_level:
                    sections_by_level[level] = []
                sections_by_level[level].append(text_item.section_name)

        # 检查缺失的必需章节
        required_sections = ["目录", "范围", "职责", "作业内容", "相关文件", "记录文件"]
        missing_sections = []
        for required in required_sections:
            found = False
            for section in sections:
                if required in section:
                    found = True
                    break
            if not found:
                missing_sections.append(required)

        return {
            "total_sections": len(sections),
            "sections_by_level": {str(k): v for k, v in sections_by_level.items()},
            "sections_found": sections,
            "missing_sections": missing_sections
        }

    def _save_to_file(self, data: Dict[str, Any], file_name: str):
        """保存提取结果到JSON文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"extracted_contents_{file_name}_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"提取结果已保存到: {output_file}")
        except Exception as e:
            logger.error(f"保存文件失败: {e}")