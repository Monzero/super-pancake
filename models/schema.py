from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import uuid

@dataclass
class FieldSchema:
    """Field schema definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    field_name: str = ""
    description: str = ""
    data_type: str = ""
    length: Optional[int] = None
    nullable: bool = True
    primary_key: bool = False
    foreign_key_ref: str = ""
    example_values: str = ""
    tags: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'field_name': self.field_name,
            'description': self.description,
            'data_type': self.data_type,
            'length': self.length,
            'nullable': self.nullable,
            'primary_key': self.primary_key,
            'foreign_key_ref': self.foreign_key_ref,
            'example_values': self.example_values,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FieldSchema':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            field_name=data.get('field_name', ''),
            description=data.get('description', ''),
            data_type=data.get('data_type', ''),
            length=data.get('length'),
            nullable=data.get('nullable', True),
            primary_key=data.get('primary_key', False),
            foreign_key_ref=data.get('foreign_key_ref', ''),
            example_values=data.get('example_values', ''),
            tags=data.get('tags', '')
        )

@dataclass
class TableSchema:
    """Table schema definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    fields: List[FieldSchema] = field(default_factory=list)
    has_sample_data: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'fields': [field.to_dict() for field in self.fields],
            'has_sample_data': self.has_sample_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TableSchema':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            description=data.get('description', ''),
            fields=[FieldSchema.from_dict(field_data) for field_data in data.get('fields', [])],
            has_sample_data=data.get('has_sample_data', False)
        )