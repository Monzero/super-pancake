import os
import json
import shutil
import uuid
from typing import List, Optional
from datetime import datetime
import pandas as pd
from models.project import ProjectConfig, ProjectFile

class ProjectService:
    """Service for managing projects and their files"""
    
    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = projects_dir
        os.makedirs(projects_dir, exist_ok=True)
    
    def create_project(self, project_config: ProjectConfig) -> bool:
        """Create a new project"""
        try:
            project_path = os.path.join(self.projects_dir, f"{project_config.name}.json")
            if os.path.exists(project_path):
                return False  # Project already exists
            
            with open(project_path, 'w') as f:
                json.dump(project_config.to_dict(), f, indent=2)
            
            # Create project data directory
            project_data_dir = os.path.join(self.projects_dir, project_config.name)
            os.makedirs(project_data_dir, exist_ok=True)
            
            return True
        except Exception as e:
            print(f"Error creating project: {e}")
            return False
    
    def load_project(self, project_name: str) -> Optional[ProjectConfig]:
        """Load an existing project"""
        try:
            project_path = os.path.join(self.projects_dir, f"{project_name}.json")
            if not os.path.exists(project_path):
                return None
            
            with open(project_path, 'r') as f:
                data = json.load(f)
            
            return ProjectConfig.from_dict(data)
        except Exception as e:
            print(f"Error loading project: {e}")
            return None
    
    def save_project(self, project_config: ProjectConfig) -> bool:
        """Save project configuration"""
        try:
            project_path = os.path.join(self.projects_dir, f"{project_config.name}.json")
            project_config.updated_at = datetime.now()
            
            with open(project_path, 'w') as f:
                json.dump(project_config.to_dict(), f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    def list_projects(self) -> List[str]:
        """List all available projects"""
        try:
            projects = []
            for file in os.listdir(self.projects_dir):
                if file.endswith('.json'):
                    projects.append(file[:-5])  # Remove .json extension
            return sorted(projects)
        except Exception as e:
            print(f"Error listing projects: {e}")
            return []
    
    def save_uploaded_file(self, project_name: str, schema_name: str, file_type: str, 
                          uploaded_file, original_filename: str) -> Optional[ProjectFile]:
        """Save an uploaded file to the project directory"""
        try:
            # Create project directory if it doesn't exist
            project_dir = os.path.join(self.projects_dir, project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(original_filename)[1]
            stored_filename = f"{schema_name}_{file_type}_{uuid.uuid4().hex[:8]}{file_extension}"
            file_path = os.path.join(project_dir, stored_filename)
            
            # Save the file
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create ProjectFile record
            project_file = ProjectFile(
                schema_name=schema_name,
                file_type=file_type,
                original_filename=original_filename,
                stored_filename=stored_filename,
                uploaded_at=datetime.now(),
                file_size=file_size
            )
            
            return project_file
            
        except Exception as e:
            print(f"Error saving file: {e}")
            return None
    
    def load_project_file(self, project_name: str, project_file: ProjectFile) -> Optional[pd.DataFrame]:
        """Load a previously saved project file"""
        try:
            file_path = os.path.join(self.projects_dir, project_name, project_file.stored_filename)
            if not os.path.exists(file_path):
                return None
            
            # Load CSV file with cleaning for better data quality
            from utils.file_utils import FileUtils
            return FileUtils.read_csv_file(file_path, clean_data=True)
            
        except Exception as e:
            print(f"Error loading project file: {e}")
            return None
    
    def get_project_file_path(self, project_name: str, project_file: ProjectFile) -> str:
        """Get the full path to a project file"""
        return os.path.join(self.projects_dir, project_name, project_file.stored_filename)
    
    def delete_project_file(self, project_name: str, project_file: ProjectFile) -> bool:
        """Delete a project file from disk"""
        try:
            file_path = self.get_project_file_path(project_name, project_file)
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting project file: {e}")
            return False
    
    def get_project_stats(self, project_name: str) -> dict:
        """Get statistics about project files"""
        try:
            project_config = self.load_project(project_name)
            if not project_config:
                return {}
            
            stats = {
                'total_files': len(project_config.project_files),
                'schema_files': len([pf for pf in project_config.project_files if pf.file_type == 'schema']),
                'sample_files': len([pf for pf in project_config.project_files if pf.file_type == 'sample']),
                'total_size': sum(pf.file_size for pf in project_config.project_files),
                'last_updated': project_config.updated_at
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting project stats: {e}")
            return {}