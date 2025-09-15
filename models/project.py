from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
from datetime import datetime

@dataclass
class ProjectFile:
    """Represents a file associated with a project"""
    schema_name: str
    file_type: str  # 'schema' or 'sample'
    original_filename: str
    stored_filename: str
    uploaded_at: datetime
    file_size: int = 0
    
    def to_dict(self) -> Dict:
        return {
            'schema_name': self.schema_name,
            'file_type': self.file_type,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'uploaded_at': self.uploaded_at.isoformat(),
            'file_size': self.file_size
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectFile':
        return cls(
            schema_name=data['schema_name'],
            file_type=data['file_type'],
            original_filename=data['original_filename'],
            stored_filename=data['stored_filename'],
            uploaded_at=datetime.fromisoformat(data['uploaded_at']),
            file_size=data.get('file_size', 0)
        )

@dataclass
class ProjectConfig:
    """Project configuration model"""
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    input_schema_names: List[str] = field(default_factory=list)
    target_schema_name: str = ""
    data_owners: List[str] = field(default_factory=list)
    project_files: List[ProjectFile] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'input_schema_names': self.input_schema_names,
            'target_schema_name': self.target_schema_name,
            'data_owners': self.data_owners,
            'project_files': [pf.to_dict() for pf in self.project_files]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectConfig':
        project_files = []
        if 'project_files' in data:
            project_files = [ProjectFile.from_dict(pf_data) for pf_data in data['project_files']]
        
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            input_schema_names=data.get('input_schema_names', []),
            target_schema_name=data.get('target_schema_name', ''),
            data_owners=data.get('data_owners', []),
            project_files=project_files
        )
    
    def get_file(self, schema_name: str, file_type: str) -> Optional[ProjectFile]:
        """Get a specific file for a schema and type"""
        for pf in self.project_files:
            if pf.schema_name == schema_name and pf.file_type == file_type:
                return pf
        return None
    
    def add_file(self, project_file: ProjectFile):
        """Add or update a file in the project"""
        # Remove existing file with same schema_name and file_type
        self.project_files = [pf for pf in self.project_files 
                             if not (pf.schema_name == project_file.schema_name and 
                                   pf.file_type == project_file.file_type)]
        # Add the new file
        self.project_files.append(project_file)
        self.updated_at = datetime.now()
    
    def remove_file(self, schema_name: str, file_type: str):
        """Remove a file from the project"""
        self.project_files = [pf for pf in self.project_files 
                             if not (pf.schema_name == schema_name and 
                                   pf.file_type == file_type)]
        self.updated_at = datetime.now()