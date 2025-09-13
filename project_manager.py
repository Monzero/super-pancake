import json
import os
from dataclasses import dataclass, asdict
from typing import List

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

    def update_project(self, index: int, project: Project):
        if not (0 <= index < len(self.projects)):
            raise IndexError('Project index out of range')
        if any(p.name == project.name and i != index for i, p in enumerate(self.projects)):
            raise ValueError(f"Project '{project.name}' already exists")
        self.projects[index] = project
        self._save()

    def delete_project(self, index: int) -> Project:
        if not (0 <= index < len(self.projects)):
            raise IndexError('Project index out of range')
        removed = self.projects.pop(index)
        self._save()
        return removed


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


def prompt_edit_project(project: Project) -> Project:
    name = input(f"Enter project name [{project.name}]: ").strip()
    if not name:
        name = project.name

    while True:
        num_str = input(f"Number of source schemas [{project.num_source_schemas}]: ").strip()
        if not num_str:
            num_source = project.num_source_schemas
            break
        if num_str.isdigit():
            num_source = int(num_str)
            break
        print('Please enter a valid integer.')

    target_schema = input(f"Target schema name [{project.target_schema}]: ").strip()
    if not target_schema:
        target_schema = project.target_schema

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
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                selected = projects[idx]
                while True:
                    print(f"\nProject: {selected.name}")
                    print(f"Source schemas: {selected.num_source_schemas}")
                    print(f"Target schema: {selected.target_schema}")
                    print('e. Edit project')
                    print('d. Delete project')
                    print('b. Back')
                    sub_choice = input('Select an option: ').strip().lower()
                    if sub_choice == 'b':
                        break
                    if sub_choice == 'e':
                        try:
                            updated = prompt_edit_project(selected)
                            registry.update_project(idx, updated)
                            selected = updated
                            print(f"Project '{selected.name}' updated.")
                        except ValueError as e:
                            print(e)
                    elif sub_choice == 'd':
                        confirm = input(f"Delete '{selected.name}'? (y/n): ").strip().lower()
                        if confirm == 'y':
                            registry.delete_project(idx)
                            print(f"Project '{selected.name}' deleted.")
                            break
                    else:
                        print('Invalid selection.')
            else:
                print('Invalid selection.')
        else:
            print('Invalid selection.')


if __name__ == '__main__':
    main()
