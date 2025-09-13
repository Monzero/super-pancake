"""Utilities for managing simple project metadata.

The module provides a command line friendly interface for creating,
reading, updating and deleting :class:`Project` records persisted in a
JSON file.  By default ``projects.json`` in the current working directory
is used as the registry file, but a different path can be supplied when
constructing :class:`ProjectRegistry`.

Typical usage::

    registry = ProjectRegistry()
    registry.add_project(Project("demo", 2, "target_schema"))
    for project in registry.list_projects():
        print(project.name)

"""

import json
import os
from dataclasses import dataclass, asdict
from typing import List

REGISTRY_FILE = 'projects.json'

@dataclass
class Project:
    """Represent a data transformation project.

    Attributes:
        name: Unique name of the project.
        num_source_schemas: Number of source schemas the project consumes.
        target_schema: Name of the target schema produced by the project.
    """

    name: str
    num_source_schemas: int
    target_schema: str


class ProjectRegistry:
    """CRUD interface for managing :class:`Project` entries.

    Args:
        path: Location of the registry JSON file. Defaults to
            :data:`REGISTRY_FILE`.
    """

    def __init__(self, path: str = REGISTRY_FILE):
        """Create a registry bound to ``path``.

        Args:
            path: Location of the registry JSON file.
        """

        print(f"Initializing ProjectRegistry with path '{path}'.")
        self.path = path
        # In-memory list of projects currently loaded.
        self.projects: List[Project] = []
        self._load()

    def _load(self):
        """Load projects from the registry file into memory."""
        print(f"Loading project registry from '{self.path}'.")
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.projects = [Project(**p) for p in data]
                    print(f"Loaded {len(self.projects)} project(s).")
            except json.JSONDecodeError:
                # Error branch: registry exists but is corrupted.
                print("Error decoding registry file; starting with empty list.")
                self.projects = []
        else:
            # Error branch: registry does not exist yet.
            print("Registry file not found; starting with empty list.")
            self.projects = []

    def _save(self):
        """Persist the in-memory project list to the registry file."""
        print(f"Saving project registry to '{self.path}'.")
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump([asdict(p) for p in self.projects], f, indent=2)

    def list_projects(self) -> List[Project]:
        """Return all currently registered projects."""
        print("Listing projects.")
        return self.projects

    def add_project(self, project: Project):
        """Create a new project entry.

        Args:
            project: The project to add.

        Raises:
            ValueError: If a project with the same name already exists.
        """

        print(f"Attempting to add project '{project.name}'.")
        if any(p.name == project.name for p in self.projects):
            print(f"Error: project '{project.name}' already exists.")
            raise ValueError(f"Project '{project.name}' already exists")
        self.projects.append(project)
        print(f"Project '{project.name}' added.")
        self._save()

    def update_project(self, index: int, project: Project):
        """Update an existing project.

        Args:
            index: List index of the project to replace.
            project: The new project data.

        Raises:
            IndexError: If ``index`` is out of range.
            ValueError: If updating would duplicate another project's name.
        """

        print(f"Attempting to update project at index {index}.")
        if not (0 <= index < len(self.projects)):
            print("Error: index out of range.")
            raise IndexError('Project index out of range')
        if any(p.name == project.name and i != index for i, p in enumerate(self.projects)):
            print(f"Error: project '{project.name}' already exists.")
            raise ValueError(f"Project '{project.name}' already exists")
        self.projects[index] = project
        print(f"Project at index {index} updated to '{project.name}'.")
        self._save()

    def delete_project(self, index: int) -> Project:
        """Delete a project from the registry.

        Args:
            index: List index of the project to remove.

        Returns:
            The :class:`Project` instance that was removed.

        Raises:
            IndexError: If ``index`` is out of range.
        """

        print(f"Attempting to delete project at index {index}.")
        if not (0 <= index < len(self.projects)):
            print("Error: index out of range.")
            raise IndexError('Project index out of range')
        removed = self.projects.pop(index)
        print(f"Project '{removed.name}' deleted.")
        self._save()
        return removed


def prompt_new_project() -> Project:
    """Interactively gather data for a new :class:`Project`."""

    # Prompt for project name.
    name = input('Enter project name: ').strip()
    while not name:
        name = input('Project name cannot be empty. Enter project name: ').strip()

    while True:
        num_str = input('Number of source schemas: ').strip()
        if num_str.isdigit():
            num_source = int(num_str)
            break
        # Error branch: non-integer input.
        print('Please enter a valid integer.')

    target_schema = input('Target schema name: ').strip()
    while not target_schema:
        # Error branch: empty target schema.
        target_schema = input('Target schema name cannot be empty. Target schema name: ').strip()

    return Project(name=name, num_source_schemas=num_source, target_schema=target_schema)


def prompt_edit_project(project: Project) -> Project:
    """Prompt the user to edit an existing :class:`Project`."""

    # Ask for a new name, defaulting to the current one.
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
        # Error branch: non-integer input.
        print('Please enter a valid integer.')

    target_schema = input(f"Target schema name [{project.target_schema}]: ").strip()
    if not target_schema:
        # No change if user leaves the field empty.
        target_schema = project.target_schema

    return Project(name=name, num_source_schemas=num_source, target_schema=target_schema)


def main():
    """Run a small command-line interface for managing projects."""

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
