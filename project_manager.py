import json
import os
from dataclasses import dataclass, asdict
from typing import List, Dict

REGISTRY_FILE = 'projects.json'

@dataclass
class Project:
    name: str
    num_source_schemas: int
    target_schema: str

class ProjectRegistry:
    def __init__(self, path: str = REGISTRY_FILE):
        self.path = path
        self.projects: List[Project] = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.projects = [Project(**p) for p in data]
            except json.JSONDecodeError:
                self.projects = []
        else:
            self.projects = []

    def _save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump([asdict(p) for p in self.projects], f, indent=2)

    def list_projects(self) -> List[Project]:
        return self.projects

    def add_project(self, project: Project):
        if any(p.name == project.name for p in self.projects):
            raise ValueError(f"Project '{project.name}' already exists")
        self.projects.append(project)
        self._save()


def prompt_new_project() -> Project:
    name = input('Enter project name: ').strip()
    while not name:
        name = input('Project name cannot be empty. Enter project name: ').strip()

    while True:
        num_str = input('Number of source schemas: ').strip()
        if num_str.isdigit():
            num_source = int(num_str)
            break
        print('Please enter a valid integer.')

    target_schema = input('Target schema name: ').strip()
    while not target_schema:
        target_schema = input('Target schema name cannot be empty. Target schema name: ').strip()

    return Project(name=name, num_source_schemas=num_source, target_schema=target_schema)


def main():
    registry = ProjectRegistry()

    while True:
        print('\n=== Project Registry ===')
        projects = registry.list_projects()
        if projects:
            for idx, p in enumerate(projects, start=1):
                print(f"{idx}. {p.name} (sources: {p.num_source_schemas}, target: {p.target_schema})")
        else:
            print('No projects found.')
        print('n. Create new project')
        print('q. Quit')
        choice = input('Select an option: ').strip().lower()

        if choice == 'q':
            break
        if choice == 'n':
            try:
                project = prompt_new_project()
                registry.add_project(project)
                print(f"Project '{project.name}' created.")
            except ValueError as e:
                print(e)
        else:
            print('Invalid selection.')


if __name__ == '__main__':
    main()
