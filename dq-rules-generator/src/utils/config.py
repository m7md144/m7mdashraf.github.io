"""
Configuration Management
========================

Handles application configuration and settings.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from pathlib import Path
import yaml
import json


@dataclass
class Config:
    """Application configuration"""
    
    # Input settings
    system_name: str = "System"
    database_name: str = "Database"
    default_schema: str = "dbo"
    
    # Rule generation settings
    timeliness_threshold_days: int = 30
    critical_fields: List[str] = field(default_factory=list)
    min_relationship_confidence: float = 0.6
    
    # Output settings
    output_directory: str = "./output"
    include_sql_file: bool = True
    include_summary: bool = True
    
    # Column mapping overrides
    column_mappings: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from YAML file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    @classmethod
    def from_json(cls, path: str) -> "Config":
        """Load configuration from JSON file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
    
    def to_yaml(self, path: str):
        """Save configuration to YAML file"""
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.__dict__, f, allow_unicode=True, default_flow_style=False)
    
    def to_json(self, path: str):
        """Save configuration to JSON file"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, ensure_ascii=False, indent=2)
