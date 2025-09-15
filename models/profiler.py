from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class FieldProfile:
    """Field profiling results"""
    field_id: str
    field_name: str
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'field_id': self.field_id,
            'field_name': self.field_name,
            'statistics': self.statistics
        }

@dataclass
class TableProfile:
    """Table profiling results"""
    table_id: str
    table_name: str
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'table_id': self.table_id,
            'table_name': self.table_name,
            'statistics': self.statistics
        }

@dataclass
class ProfilerResults:
    """Complete profiler results"""
    field_profiles: Dict[str, FieldProfile] = field(default_factory=dict)
    table_profiles: Dict[str, TableProfile] = field(default_factory=dict)
    quality_issues: List[Dict] = field(default_factory=list)
    schema_summary: Dict[str, Any] = field(default_factory=dict)