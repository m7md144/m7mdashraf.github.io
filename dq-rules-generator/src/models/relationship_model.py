"""
Relationship Models
===================

Models for representing table relationships,
including inferred relationships without explicit FKs.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class RelationshipType(Enum):
    """Type of relationship between tables"""
    FOREIGN_KEY = "ForeignKey"           # Explicit FK constraint
    INFERRED_NAME = "InferredByName"     # Same column name pattern
    INFERRED_TYPE = "InferredByType"     # Same data type + naming pattern
    INFERRED_VALUES = "InferredByValues" # Matching values in data
    INFERRED_DESC = "InferredByDesc"     # Description mentions relationship
    BUSINESS_LOGIC = "BusinessLogic"     # Domain-specific business rule


class RelationshipStrength(Enum):
    """Confidence level of relationship inference"""
    DEFINITE = "Definite"      # Explicit FK or 100% match
    HIGH = "High"              # Strong pattern match (>90%)
    MEDIUM = "Medium"          # Moderate confidence (70-90%)
    LOW = "Low"                # Weak inference (<70%)


@dataclass
class TableRelationship:
    """
    Represents a relationship between two tables.
    
    Can be explicit (FK) or inferred through pattern analysis.
    """
    
    # Source table (the one with the foreign key / reference)
    source_schema: str
    source_table: str
    source_column: str
    
    # Target table (the one being referenced)
    target_schema: str
    target_table: str
    target_column: str
    
    # Relationship metadata
    relationship_type: RelationshipType = RelationshipType.INFERRED_NAME
    strength: RelationshipStrength = RelationshipStrength.MEDIUM
    confidence_score: float = 0.0  # 0.0 to 1.0
    
    # Business context
    business_meaning: str = ""  # Arabic description of the relationship
    validation_impact: str = "" # Impact if relationship is violated
    
    # Evidence for inference
    inference_reasons: List[str] = field(default_factory=list)
    
    @property
    def source_full_name(self) -> str:
        if self.source_schema:
            return f"{self.source_schema}.{self.source_table}"
        return self.source_table
    
    @property
    def target_full_name(self) -> str:
        if self.target_schema:
            return f"{self.target_schema}.{self.target_table}"
        return self.target_table
    
    def get_validation_sql(self, database: str = "") -> str:
        """Generate SQL to validate referential integrity"""
        db_prefix = f"[{database}]." if database else ""
        
        return f"""-- التحقق من سلامة العلاقة: {self.source_table}.{self.source_column} -> {self.target_table}.{self.target_column}
SELECT 
    src.[{self.source_column}],
    '{self.source_table}' AS SourceTable,
    '{self.target_table}' AS ExpectedTarget
FROM {db_prefix}[{self.source_schema}].[{self.source_table}] src
LEFT JOIN {db_prefix}[{self.target_schema}].[{self.target_table}] tgt
    ON src.[{self.source_column}] = tgt.[{self.target_column}]
WHERE src.[{self.source_column}] IS NOT NULL
  AND tgt.[{self.target_column}] IS NULL"""
    
    def to_dict(self) -> dict:
        return {
            "source_table": self.source_full_name,
            "source_column": self.source_column,
            "target_table": self.target_full_name,
            "target_column": self.target_column,
            "type": self.relationship_type.value,
            "strength": self.strength.value,
            "confidence": self.confidence_score,
            "business_meaning": self.business_meaning,
            "reasons": self.inference_reasons
        }


@dataclass
class RelationshipInferenceResult:
    """Result of relationship inference analysis"""
    
    relationships: List[TableRelationship] = field(default_factory=list)
    orphan_tables: List[str] = field(default_factory=list)  # Tables with no relationships
    analysis_notes: List[str] = field(default_factory=list)
    
    def get_relationships_for_table(self, table_name: str) -> List[TableRelationship]:
        """Get all relationships involving a specific table"""
        results = []
        table_lower = table_name.lower()
        for rel in self.relationships:
            if (rel.source_table.lower() == table_lower or 
                rel.target_table.lower() == table_lower):
                results.append(rel)
        return results
    
    def get_high_confidence_relationships(self) -> List[TableRelationship]:
        """Get relationships with high or definite confidence"""
        return [r for r in self.relationships 
                if r.strength in [RelationshipStrength.DEFINITE, RelationshipStrength.HIGH]]
