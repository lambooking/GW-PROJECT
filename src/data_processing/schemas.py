"""
定义用于文档预处理的标准化数据结构。
使用Pydantic模型确保数据的一致性和类型安全，与技术路线文档中的JSON格式对应。
"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    """文档元信息"""
    scene_type: Optional[str] = Field(None, description="场景类型，例如 'scenario_one' 或 'scenario_two'")
    scene_name: Optional[str] = Field(None, description="场景名称，例如 '作业指导书'")
    file_name: str = Field(description="原始文件名")
    total_pages: int = Field(description="文档总页数")
    processing_timestamp: datetime = Field(description="处理开始时间戳")
    classification_confidence: Optional[float] = Field(None, description="分类置信度")

class TextContent(BaseModel):
    """结构化文本内容"""
    section_type: str = Field(description="段落类型，如 'title' (标题), 'content' (正文), 'table_caption' (表格标题), 'image_caption' (图片标题)")
    section_name: Optional[str] = Field(None, description="章节名称，如 '1.1 职责'")
    content: str = Field(description="段落的具体文本内容")
    page_number: int = Field(description="所在页码")
    hierarchy_level: Optional[int] = Field(None, description="内容在文档中的层级，如1级标题、2级标题")
    word_count: int = Field(description="内容的字数")

class Table(BaseModel):
    """结构化表格内容"""
    table_id: str = Field(description="表格的唯一标识符，例如 'table_1'")
    caption: Optional[str] = Field(None, description="表格标题")
    headers: List[str] = Field(default_factory=list, description="表格的表头")
    data: List[List[Any]] = Field(description="表格数据，为二维列表")
    page_number: int = Field(description="所在页码")
    table_type: Optional[str] = Field(None, description="表格类型，如 'parameter', 'personnel' (此项由下游模型分析确定)")

class Image(BaseModel):
    """结构化图像内容"""
    image_id: str = Field(description="图片的唯一标识符，例如 'img_1'")
    type: Optional[str] = Field(None, description="图片类型，如 'route_map', 'signature_page' (此项由下游模型分析确定)")
    base64_data: str = Field(description="图片的Base64编码字符串")
    extracted_text: Optional[str] = Field(None, description="从图片中提取的OCR文本")
    page_number: int = Field(description="所在页码")
    description: Optional[str] = Field(None, description="图片描述或标题")

class StandardizedDocument(BaseModel):
    """
    文档预处理后的标准化输出格式，是整个处理流程中传递的核心数据结构。
    """
    document_info: DocumentInfo
    text_content: List[TextContent] = Field(default_factory=list)
    tables: List[Table] = Field(default_factory=list)
    images: List[Image] = Field(default_factory=list)
