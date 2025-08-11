"""
Configuration manager for the RAG Scoring System.
"""

import yaml
import json
import os
from typing import Any, Dict, Optional, Union
from pathlib import Path
from dataclasses import asdict

from .schemas import Config, SystemConfig, VLLMConfig, KnowledgeBaseConfig, ScoringConfig, ProcessingConfig, OutputConfig
from ..core.exceptions import ConfigurationError


class ConfigManager:
    """Unified configuration manager."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize configuration manager."""
        self._config_path = Path(config_path) if config_path else Path("config")
        self._config = Config()
        self._loaded = False
        
        self.load_configuration()
    
    def load_configuration(self) -> None:
        """Load configuration from various sources."""
        try:
            # Load from YAML file
            yaml_config = self._load_yaml_config()
            if yaml_config:
                self._merge_config(yaml_config)
            
            # Override with environment variables
            self._load_env_config()
            
            # Validate configuration
            self._validate_config()
            
            self._loaded = True
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _load_yaml_config(self) -> Optional[Dict[str, Any]]:
        """Load configuration from YAML file."""
        if self._config_path.is_file():
            config_file = self._config_path
        else:
            config_file = self._config_path / "config.yaml"
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to load YAML config from {config_file}: {e}")
    
    def _merge_config(self, yaml_config: Dict[str, Any]) -> None:
        """Merge YAML configuration into the config object."""
        # System configuration
        if 'system' in yaml_config:
            system_data = yaml_config['system']
            self._config.system = SystemConfig(
                debug=system_data.get('debug', self._config.system.debug),
                log_level=system_data.get('log_level', self._config.system.log_level),
                max_workers=system_data.get('max_workers', self._config.system.max_workers),
                timeout=system_data.get('timeout', self._config.system.timeout),
                temp_dir=system_data.get('temp_dir', self._config.system.temp_dir)
            )
        
        # VLLM configuration
        if 'vllm' in yaml_config:
            vllm_data = yaml_config['vllm']
            self._config.vllm = VLLMConfig(
                host=vllm_data.get('host', self._config.vllm.host),
                port=vllm_data.get('port', self._config.vllm.port),
                model_name=vllm_data.get('model_name', self._config.vllm.model_name),
                api_key=vllm_data.get('api_key', self._config.vllm.api_key),
                max_tokens=vllm_data.get('max_tokens', self._config.vllm.max_tokens),
                temperature=vllm_data.get('temperature', self._config.vllm.temperature),
                timeout=vllm_data.get('timeout', self._config.vllm.timeout)
            )
        
        # Knowledge base configuration
        if 'knowledge_base' in yaml_config:
            kb_data = yaml_config['knowledge_base']
            self._config.knowledge_base = KnowledgeBaseConfig(
                storage_type=kb_data.get('storage_type', self._config.knowledge_base.storage_type),
                storage_path=kb_data.get('storage_path', self._config.knowledge_base.storage_path),
                embedding_model=kb_data.get('embedding_model', self._config.knowledge_base.embedding_model),
                chunk_size=kb_data.get('chunk_size', self._config.knowledge_base.chunk_size),
                chunk_overlap=kb_data.get('chunk_overlap', self._config.knowledge_base.chunk_overlap),
                collection_name=kb_data.get('collection_name', self._config.knowledge_base.collection_name)
            )
        
        # Processing configuration
        if 'processing' in yaml_config:
            proc_data = yaml_config['processing']
            self._config.processing = ProcessingConfig(
                supported_formats=proc_data.get('supported_formats', self._config.processing.supported_formats),
                max_file_size_mb=proc_data.get('max_file_size_mb', self._config.processing.max_file_size_mb),
                ocr_enabled=proc_data.get('ocr_enabled', self._config.processing.ocr_enabled),
                image_extraction=proc_data.get('image_extraction', self._config.processing.image_extraction),
                table_extraction=proc_data.get('table_extraction', self._config.processing.table_extraction),
                temp_cleanup=proc_data.get('temp_cleanup', self._config.processing.temp_cleanup)
            )
        
        # Output configuration
        if 'output' in yaml_config:
            output_data = yaml_config['output']
            self._config.output = OutputConfig(
                reports_dir=output_data.get('reports_dir', self._config.output.reports_dir),
                html_reports_dir=output_data.get('html_reports_dir', self._config.output.html_reports_dir),
                json_reports_dir=output_data.get('json_reports_dir', self._config.output.json_reports_dir),
                logs_dir=output_data.get('logs_dir', self._config.output.logs_dir),
                enable_html_reports=output_data.get('enable_html_reports', self._config.output.enable_html_reports),
                enable_json_reports=output_data.get('enable_json_reports', self._config.output.enable_json_reports)
            )
        
        # Scoring configuration - keep existing logic for now
        self._config.scoring = ScoringConfig()
    
    def _load_env_config(self) -> None:
        """Load configuration from environment variables."""
        # VLLM configuration
        if os.getenv('VLLM_HOST'):
            self._config.vllm.host = os.getenv('VLLM_HOST')
        if os.getenv('VLLM_PORT'):
            self._config.vllm.port = int(os.getenv('VLLM_PORT'))
        if os.getenv('VLLM_MODEL_NAME'):
            self._config.vllm.model_name = os.getenv('VLLM_MODEL_NAME')
        if os.getenv('VLLM_API_KEY'):
            self._config.vllm.api_key = os.getenv('VLLM_API_KEY')
        
        # System configuration
        if os.getenv('RAG_DEBUG'):
            self._config.system.debug = os.getenv('RAG_DEBUG').lower() == 'true'
        if os.getenv('RAG_LOG_LEVEL'):
            self._config.system.log_level = os.getenv('RAG_LOG_LEVEL')
        if os.getenv('RAG_MAX_WORKERS'):
            self._config.system.max_workers = int(os.getenv('RAG_MAX_WORKERS'))
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        # Validate VLLM configuration
        if not (1 <= self._config.vllm.port <= 65535):
            raise ConfigurationError(f"Invalid VLLM port: {self._config.vllm.port}")
        
        if not (0.0 <= self._config.vllm.temperature <= 2.0):
            raise ConfigurationError(f"Invalid VLLM temperature: {self._config.vllm.temperature}")
        
        # Validate system configuration
        if self._config.system.max_workers <= 0:
            raise ConfigurationError(f"Invalid max_workers: {self._config.system.max_workers}")
        
        # Validate knowledge base configuration
        if self._config.knowledge_base.chunk_size <= 0:
            raise ConfigurationError(f"Invalid chunk_size: {self._config.knowledge_base.chunk_size}")
        
        # Create necessary directories
        for dir_path in [
            self._config.output.reports_dir,
            self._config.output.html_reports_dir,
            self._config.output.json_reports_dir,
            self._config.output.logs_dir,
            self._config.knowledge_base.storage_path,
            self._config.system.temp_dir
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key."""
        if not self._loaded:
            raise ConfigurationError("Configuration not loaded")
        
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-separated key."""
        keys = key.split('.')
        config_obj = self._config
        
        # Navigate to the parent object
        for k in keys[:-1]:
            if hasattr(config_obj, k):
                config_obj = getattr(config_obj, k)
            else:
                raise ConfigurationError(f"Invalid configuration key: {key}")
        
        # Set the final value
        final_key = keys[-1]
        if hasattr(config_obj, final_key):
            setattr(config_obj, final_key, value)
        else:
            raise ConfigurationError(f"Invalid configuration key: {key}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary."""
        return {
            "system": asdict(self._config.system),
            "vllm": {
                **asdict(self._config.vllm),
                "api_key": "***" if self._config.vllm.api_key else None
            },
            "knowledge_base": asdict(self._config.knowledge_base),
            "processing": asdict(self._config.processing),
            "output": asdict(self._config.output)
        }
    
    def export_config(self, output_path: Union[str, Path], format: str = "yaml") -> None:
        """Export current configuration to file."""
        output_path = Path(output_path)
        config_dict = asdict(self._config)
        
        try:
            if format.lower() == "yaml":
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            elif format.lower() == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
            else:
                raise ConfigurationError(f"Unsupported export format: {format}")
        except Exception as e:
            raise ConfigurationError(f"Failed to export configuration: {e}")
    
    @property
    def system(self) -> SystemConfig:
        """Get system configuration."""
        return self._config.system
    
    @property
    def vllm(self) -> VLLMConfig:
        """Get VLLM configuration."""
        return self._config.vllm
    
    @property
    def knowledge_base(self) -> KnowledgeBaseConfig:
        """Get knowledge base configuration."""
        return self._config.knowledge_base
    
    @property
    def scoring(self) -> ScoringConfig:
        """Get scoring configuration."""
        return self._config.scoring
    
    @property
    def processing(self) -> ProcessingConfig:
        """Get processing configuration."""
        return self._config.processing
    
    @property
    def output(self) -> OutputConfig:
        """Get output configuration."""
        return self._config.output