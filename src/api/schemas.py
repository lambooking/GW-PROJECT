"""
API数据模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class AuditResultResponse(BaseModel):
    """审核结果响应模型"""
    status: str = Field(..., description="处理状态")
    filename: str = Field(..., description="文件名")
    results: Dict[str, Any] = Field(..., description="审核结果")
    report_url: Optional[str] = Field(None, description="报告链接")


class BatchAuditResponse(BaseModel):
    """批量审核响应模型"""
    status: str = Field(..., description="处理状态")
    total_files: int = Field(..., description="总文件数")
    results: List[Dict[str, Any]] = Field(..., description="审核结果列表")
    report_url: Optional[str] = Field(None, description="报告链接")
    excel_url: Optional[str] = Field(None, description="Excel报告链接")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="系统状态")
    message: str = Field(..., description="状态消息")
    components: Dict[str, str] = Field(..., description="组件状态")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    detail: str = Field(..., description="错误详情") 