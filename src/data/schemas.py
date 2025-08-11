"""
Standard data schemas for the RAG Scoring System.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    """Document metadata information."""
    scene_type: Optional[str] = Field(None, description="Scene type: 'scenario_1' or 'scenario_2'")
    scene_name: Optional[str] = Field(None, description="Scene name in Chinese")
    file_name: str = Field(description="Original filename")
    file_path: str = Field(description="File path")
    total_pages: int = Field(description="Total number of pages")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    processing_timestamp: datetime = Field(default_factory=datetime.now, description="Processing timestamp")
    classification_confidence: Optional[float] = Field(None, description="Classification confidence score")


class TextContent(BaseModel):
    """Structured text content."""
    section_type: str = Field(description="Section type: 'title', 'content', 'table_caption', 'image_caption'")
    section_name: Optional[str] = Field(None, description="Section name like '1.1 职责'")
    content: str = Field(description="Text content")
    page_number: int = Field(description="Page number")
    hierarchy_level: Optional[int] = Field(None, description="Hierarchy level in document")
    word_count: int = Field(description="Word count")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Position coordinates in page")


class Table(BaseModel):
    """Structured table content."""
    table_id: str = Field(description="Unique table identifier")
    caption: Optional[str] = Field(None, description="Table caption")
    headers: List[str] = Field(default_factory=list, description="Table headers")
    data: List[List[Any]] = Field(description="Table data as 2D array")
    page_number: int = Field(description="Page number")
    table_type: Optional[str] = Field(None, description="Table type")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Position coordinates in page")


class Image(BaseModel):
    """Structured image content."""
    image_id: str = Field(description="Unique image identifier")
    image_type: Optional[str] = Field(None, description="Image type")
    base64_data: str = Field(description="Base64 encoded image data")
    extracted_text: Optional[str] = Field(None, description="OCR extracted text")
    page_number: int = Field(description="Page number")
    description: Optional[str] = Field(None, description="Image description")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Position coordinates in page")


class StandardizedDocument(BaseModel):
    """
    Standardized document format after preprocessing.
    Core data structure for the entire processing pipeline.
    """
    document_info: DocumentInfo
    text_content: List[TextContent] = Field(default_factory=list)
    tables: List[Table] = Field(default_factory=list)
    images: List[Image] = Field(default_factory=list)
    raw_content: Optional[str] = Field(None, description="Raw text content for fallback")
    
    def get_full_text(self) -> str:
        """Get concatenated text content."""
        if self.raw_content:
            return self.raw_content
        
        text_parts = []
        for text in self.text_content:
            text_parts.append(text.content)
        return "\n".join(text_parts)
    
    def get_tables_text(self) -> str:
        """Get concatenated table content as text."""
        table_texts = []
        for table in self.tables:
            if table.caption:
                table_texts.append(f"表格: {table.caption}")
            
            if table.headers:
                table_texts.append(" | ".join(table.headers))
            
            for row in table.data:
                table_texts.append(" | ".join(str(cell) for cell in row))
            
            table_texts.append("")  # Empty line between tables
        
        return "\n".join(table_texts)
    
    def get_images_text(self) -> str:
        """Get concatenated image OCR text."""
        image_texts = []
        for image in self.images:
            if image.description:
                image_texts.append(f"图像描述: {image.description}")
            if image.extracted_text:
                image_texts.append(f"图像文字: {image.extracted_text}")
        return "\n".join(image_texts)


class ScoreItem(BaseModel):
    """Individual scoring item."""
    name: str = Field(description="Score item name")
    score: float = Field(description="Score value")
    max_score: float = Field(description="Maximum possible score")
    weight: float = Field(description="Weight in final score")
    reason: str = Field(description="Scoring reason")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


class ScoringResult(BaseModel):
    """Complete scoring result."""
    document_info: DocumentInfo
    scenario: str = Field(description="Scoring scenario")
    total_score: float = Field(description="Total score")
    max_total_score: float = Field(description="Maximum total score")
    score_percentage: float = Field(description="Score percentage")
    score_items: List[ScoreItem] = Field(description="Detailed scoring items")
    processing_time: float = Field(description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now)
    summary: Optional[str] = Field(None, description="Overall summary")
    
    def get_score_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed score breakdown."""
        breakdown = {}
        for item in self.score_items:
            breakdown[item.name] = {
                "score": item.score,
                "max_score": item.max_score,
                "percentage": (item.score / item.max_score * 100) if item.max_score > 0 else 0,
                "weight": item.weight,
                "reason": item.reason,
                "evidence": item.evidence,
                "suggestions": item.suggestions
            }
        return breakdown