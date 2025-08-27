"""
文档预处理流水线，负责协调整个文档处理流程。
"""
import base64
import logging
from datetime import datetime
import time
from pathlib import Path
from typing import Dict, Any

from .document_classifier import DocumentClassifier
from .document_parser import DocumentParser
from .enhanced_pdf_parser import EnhancedPDFParser
from .schemas import (StandardizedDocument, DocumentInfo, TextContent, Table, Image)

logger = logging.getLogger(__name__)

class PreprocessingPipeline:
    """
    文档预处理的总协调器。
    该流水线按顺序执行以下步骤：
    1. 根据文件类型选择合适的解析器 (DOCX, PDF)。
    2. 对解析出的原生内容进行场景分类。
    3. 将解析和分类的结果转换为标准化的数据格式 (StandardizedDocument)。
    """

    def __init__(self, enable_enhanced_ocr: bool = False):
        """初始化各个处理模块

        Args:
            enable_enhanced_ocr: 是否启用增强OCR（兼容测试参数，不影响当前实现）
        """
        self.docx_parser = DocumentParser()
        self.pdf_parser = EnhancedPDFParser()
        self.classifier = DocumentClassifier()
        self.enable_enhanced_ocr = enable_enhanced_ocr
        # OCR引擎可以在解析器内部初始化，这里我们假设解析器自带OCR能力
        
    def process(self, file_path: str) -> StandardizedDocument:
        """
        执行完整的文档预处理流程。

        Args:
            file_path: 指向待处理文档的路径。

        Returns:
            一个包含标准化文档数据的Pydantic模型实例。
            
        Raises:
            FileNotFoundError: 如果文件不存在。
            ValueError: 如果文件格式不被支持。
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_suffix = path.suffix.lower()
        
        # 1. 解析文档
        if file_suffix == '.docx':
            # 注意：当前的DocumentParser会返回一个自定义字典
            raw_parsed_data = self.docx_parser.parse_docx(path)
        elif file_suffix == '.pdf':
            # EnhancedPDFParser返回一个更详细的字典
            raw_parsed_data = self.pdf_parser.parse_pdf_enhanced(path)
        else:
            raise ValueError(f"不支持的文件格式: {file_suffix}")
            
        # 2. 场景分类
        classification_result = self.classifier.classify_document(raw_parsed_data)
        
        # 3. 结果标准化
        standardized_output = self._standardize_output(
            raw_data=raw_parsed_data,
            classification=classification_result,
            file_path=path
        )
        
        return standardized_output

    # 兼容脚本测试：提供更高层的包装方法
    def process_document(self, file_path: str, include_ocr: bool = True) -> Dict[str, Any]:
        """处理单个文档并返回可序列化字典（用于测试与报告）。"""
        start_total = time.perf_counter()

        file_path_obj = Path(file_path)
        file_type = file_path_obj.suffix.lower().lstrip('.')

        # 分步计时（当前实现主要以总时间为主，其他步骤可为占位）
        t1 = time.perf_counter()
        document = self.process(file_path)
        step_total = time.perf_counter() - t1

        total_time = time.perf_counter() - start_total

        # 构建可输出结果
        content_stats = {
            "text_sections": len(document.text_content),
            "tables": len(document.tables),
            "images": len(document.images),
        }

        entity_stats = {
            "dates": 0,
            "personnel": 0,
            "technical_parameters": 0,
            "locations": 0,
            "standards": 0,
            "organizations": 0,
        }

        performance_metrics = {
            "step1_parsing": step_total,
            "step2_extraction": 0.0,
            "step3_fusion": 0.0,
            "step4_entities": 0.0,
            "step5_ocr": 0.0 if include_ocr else 0.0,
            "total_time": total_time,
        }

        classification = {
            "scenario": document.document_info.scene_type,
            "scenario_name": document.document_info.scene_name,
            "confidence": document.document_info.classification_confidence or 0.0,
        }

        file_info = {
            "file_type": file_type,
            "total_pages": document.document_info.total_pages,
        }

        quality_assessment = {
            "overall_quality_score": 0.0,
            "quality_grade": "N/A",
        }

        result = {
            "status": "success",
            "file_info": file_info,
            "classification": classification,
            "document_profile": {
                "content_statistics": content_stats,
                "entity_statistics": entity_stats,
            },
            "performance_metrics": performance_metrics,
            "analysis_ready_data": {
                "key_entities": {
                    "dates": [],
                    "personnel": [],
                    "technical_parameters": [],
                }
            },
            "quality_assessment": quality_assessment,
        }

        return result

    def process_document_batch(self, file_paths: list[str], include_ocr: bool = False) -> Dict[str, Any]:
        """批量处理文档并返回概要统计。"""
        batch_start = time.perf_counter()
        results = []
        success = 0
        for path in file_paths:
            try:
                res = self.process_document(path, include_ocr=include_ocr)
                results.append({"file": path, "success": True, "result": res})
                success += 1
            except Exception as e:  # 保持健壮性
                results.append({"file": path, "success": False, "error": str(e)})

        total_time = time.perf_counter() - batch_start
        total_files = len(file_paths)
        summary = {
            "total_files": total_files,
            "successful_files": success,
            "failed_files": total_files - success,
            "success_rate": (success / total_files * 100.0) if total_files else 0.0,
            "total_processing_time": total_time,
            "average_time_per_file": (total_time / total_files) if total_files else 0.0,
        }

        return {
            "results": results,
            "batch_summary": summary,
        }

    def _standardize_output(self, raw_data: Dict[str, Any], classification: Dict[str, Any], file_path: Path) -> StandardizedDocument:
        """
        将解析器和分类器的原始输出转换为标准化的Pydantic模型。
        这是确保数据一致性的核心步骤。
        
        Args:
            raw_data: 来自DOCX或PDF解析器的原始字典。
            classification: 来自DocumentClassifier的分类结果。
            file_path: 文件路径对象。

        Returns:
            StandardizedDocument的实例。
        """
        # 1. 创建DocumentInfo
        doc_info = DocumentInfo(
            scene_type=classification.get("scenario"),
            scene_name=classification.get("scenario_name"),
            file_name=file_path.name,
            total_pages=raw_data.get("total_pages", 0),
            processing_timestamp=datetime.now(),
            classification_confidence=classification.get("confidence")
        )

        # 2. 标准化文本内容
        text_contents = self._standardize_text(raw_data.get("text_content", []))
        
        # 3. 标准化表格
        tables = self._standardize_tables(raw_data.get("tables", []))
        
        # 4. 标准化图片
        images = self._standardize_images(raw_data.get("images", []))

        # 5. 组装最终对象
        standardized_doc = StandardizedDocument(
            document_info=doc_info,
            text_content=text_contents,
            tables=tables,
            images=images
        )
        
        return standardized_doc

    def _standardize_text(self, raw_texts: list) -> list[TextContent]:
        """标准化文本内容"""
        standardized = []
        for item in raw_texts:
            content = item.get("content", "")
            # EnhancedPDFParser的输出更丰富
            section_type = "title" if item.get("type") == "header" else "content"
            level = item.get("level") 
            # DOCX的简单输出
            if "style" in item and "heading" in item["style"].lower():
                 section_type = "title"
                 try:
                    level = int(item["style"][-1])
                 except (ValueError, IndexError):
                    level = 1

            standardized.append(
                TextContent(
                    section_type=section_type,
                    section_name=content.split('\n')[0] if section_type=="title" else None,
                    content=content,
                    page_number=item.get("page_number", 0), # docx无页码信息，暂定为0
                    hierarchy_level=level,
                    word_count=len(content)
                )
            )
        return standardized

    def _standardize_tables(self, raw_tables: list) -> list[Table]:
        """标准化表格内容"""
        standardized = []
        for i, item in enumerate(raw_tables):
            data = item.get("data", [])
            headers = data[0] if data else []
            body = data[1:] if len(data) > 1 else []
            
            standardized.append(
                Table(
                    table_id=f"table_{i+1}",
                    caption=item.get("caption"), # 当前解析器未提供
                    headers=headers,
                    data=body,
                    page_number=item.get("page_number", 0) # docx无页码信息
                )
            )
        return standardized

    def _standardize_images(self, raw_images: list) -> list[Image]:
        """标准化图像内容"""
        standardized = []
        for i, item in enumerate(raw_images):
            img_data = item.get("data")
            if not img_data:
                continue

            base64_str = base64.b64encode(img_data).decode('utf-8')
            
            # 简化：不进行OCR，直接让大模型判断图片内容
            standardized.append(
                Image(
                    image_id=f"img_{i+1}",
                    base64_data=base64_str,
                    extracted_text="",  # 不进行OCR预处理
                    page_number=item.get("page_number", 0) # docx无页码信息
                )
            )
        return standardized

if __name__ == '__main__':
    print("--- 开始执行预处理流水线测试 ---")
    
    # 配置日志记录，确保INFO级别以上的日志可以被打印出来
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    # 指向测试文件
    # 使用相对路径以保证代码的可移植性
    test_file = Path(__file__).parent.parent.parent / "data" / "raw" / "场景1(1).pdf"
    
    if test_file.exists():
        logger.info(f"开始处理测试文件: {test_file}")
        pipeline = PreprocessingPipeline()
        try:
            result = pipeline.process(str(test_file))
            
            print("\n--- ✅ 预处理成功 ---")
            print(result.model_dump_json(indent=2))
            print("--------------------\n")

        except Exception as e:
            logger.error(f"处理测试文件时发生严重错误: {e}", exc_info=True)
            print(f"\n--- ❌ 预处理失败 --- \nError: {e}\n--------------------\n")
    else:
        logger.warning(f"测试文件未找到，请确认路径: {test_file}")
    
    print("--- 预处理流水线测试执行完毕 ---")

