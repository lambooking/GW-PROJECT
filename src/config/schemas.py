"""
Configuration data schemas for the RAG Scoring System.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path


@dataclass
class SystemConfig:
    """System-level configuration."""
    debug: bool = False
    log_level: str = "INFO"
    max_workers: int = 4
    timeout: int = 120
    temp_dir: str = "/tmp/rag_scoring"


@dataclass
class VLLMConfig:
    """VLLM service configuration."""
    host: str = "localhost"
    port: int = 8000
    model_name: str = "qwen2.5-vl-3b"
    api_key: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.1
    timeout: int = 60


@dataclass  
class KnowledgeBaseConfig:
    """Knowledge base configuration."""
    storage_type: str = "chromadb"  # chromadb, faiss, etc.
    storage_path: str = "output/rag_knowledge_base"
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    collection_name: str = "documents"


@dataclass
class ScoringCriteria:
    """Individual scoring criteria configuration."""
    name: str
    weight: float
    max_score: int
    description: str = ""


@dataclass
class ScoringConfig:
    """Scoring configuration for different scenarios."""
    scenario_1: Dict[str, ScoringCriteria] = field(default_factory=dict)
    scenario_2: Dict[str, ScoringCriteria] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.scenario_1:
            self.scenario_1 = {
                "structure_completeness": ScoringCriteria(
                    name="结构完整性",
                    weight=0.2,
                    max_score=20,
                    description="文档结构和目录完整性"
                ),
                "content_completeness": ScoringCriteria(
                    name="内容完整性", 
                    weight=0.3,
                    max_score=30,
                    description="文档内容完整性和准确性"
                ),
                "reference_traceability": ScoringCriteria(
                    name="引用文件可追溯性",
                    weight=0.15,
                    max_score=15,
                    description="引用文件的真实性和有效性"
                ),
                "business_logic": ScoringCriteria(
                    name="业务逻辑",
                    weight=0.2,
                    max_score=20,
                    description="业务流程逻辑合理性"
                ),
                "grammar_syntax": ScoringCriteria(
                    name="语法语句",
                    weight=0.15,
                    max_score=15,
                    description="语法错误和表达规范性"
                )
            }
        
        if not self.scenario_2:
            self.scenario_2 = {
                "image_recognition": ScoringCriteria(
                    name="图像识别",
                    weight=0.4,
                    max_score=40,
                    description="图像内容识别和分析"
                ),
                "contextual_logic": ScoringCriteria(
                    name="上下文逻辑",
                    weight=0.45,
                    max_score=45,
                    description="文档逻辑一致性检查"
                ),
                "processing_efficiency": ScoringCriteria(
                    name="处理效率",
                    weight=0.15,
                    max_score=15,
                    description="处理速度和效率"
                )
            }


@dataclass
class ProcessingConfig:
    """Document processing configuration."""
    supported_formats: List[str] = field(default_factory=lambda: [".pdf", ".docx", ".doc"])
    max_file_size_mb: int = 50
    ocr_enabled: bool = True
    image_extraction: bool = True
    table_extraction: bool = True
    temp_cleanup: bool = True


@dataclass
class OutputConfig:
    """Output and reporting configuration."""
    reports_dir: str = "output/rag_scoring_reports"
    html_reports_dir: str = "output/rag_scoring_reports/html"
    json_reports_dir: str = "output/rag_scoring_reports"
    logs_dir: str = "logs"
    enable_html_reports: bool = True
    enable_json_reports: bool = True


@dataclass
class Config:
    """Main configuration container."""
    system: SystemConfig = field(default_factory=SystemConfig)
    vllm: VLLMConfig = field(default_factory=VLLMConfig)
    knowledge_base: KnowledgeBaseConfig = field(default_factory=KnowledgeBaseConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    output: OutputConfig = field(default_factory=OutputConfig)