from __future__ import annotations

"""Dataclasses describing schemas and project configuration."""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import json

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback when PyYAML isn't available
    yaml = None


@dataclass
class FieldDefinition:
    """Definition of a single field within a schema."""

    name: str
    data_type: str
    required: bool = True
    description: Optional[str] = None
    validation: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a plain ``dict``.

        Returns:
            Dict[str, Any]: Each attribute converted to a JSON/YAML-friendly
                primitive type.

        When to use:
            Call this before serialising to JSON or YAML, or when a mutable
            dictionary representation is needed for inspection.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldDefinition":
        """Construct a :class:`FieldDefinition` from a dictionary.

        Args:
            data (Dict[str, Any]): Mapping of field attributes.

        Returns:
            FieldDefinition: Instance populated using ``data``.

        When to use:
            Use when loading field metadata from parsed JSON/YAML structures.
        """
        # Unpack the mapping directly into the dataclass constructor.
        return cls(**data)

    def to_json(self) -> str:
        """Serialise the field definition to a JSON string.

        Returns:
            str: JSON representation of this field.

        When to use:
            Use when storing or transmitting the definition in JSON format.
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, data: str) -> "FieldDefinition":
        """Create a :class:`FieldDefinition` from a JSON string.

        Args:
            data (str): JSON text representing the field.

        Returns:
            FieldDefinition: Deserialised instance.

        When to use:
            Use when reading definitions stored as JSON.
        """
        return cls.from_dict(json.loads(data))

    def to_yaml(self) -> str:
        """Serialise the field definition to YAML.

        Returns:
            str: YAML representation, or JSON if PyYAML isn't installed.

        When to use:
            Useful for human-readable configuration files.
        """
        if yaml:
            return yaml.safe_dump(self.to_dict(), sort_keys=False)
        # Fall back to JSON when the optional dependency is missing.
        print("PyYAML not installed; using JSON for FieldDefinition.to_yaml")
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_yaml(cls, data: str) -> "FieldDefinition":
        """Create a :class:`FieldDefinition` from YAML data.

        Args:
            data (str): YAML text; JSON is also accepted when PyYAML is
                unavailable.

        Returns:
            FieldDefinition: Deserialised instance.

        When to use:
            Use for loading field definitions from YAML or JSON configuration
            files.
        """
        if yaml:
            raw = yaml.safe_load(data)
        else:
            # Fall back to JSON parsing when PyYAML isn't available.
            print(
                "PyYAML not installed; parsing FieldDefinition.from_yaml as JSON"
            )
            raw = json.loads(data)
        return cls.from_dict(raw)


@dataclass
class SchemaDefinition:
    """Collection of fields describing a dataset schema."""

    name: str
    file_path: Optional[str] = None
    fields: List[FieldDefinition] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the schema definition to a dictionary.

        Returns:
            Dict[str, Any]: Mapping ready for JSON/YAML serialisation.

        When to use:
            Use prior to dumping to JSON/YAML or for direct manipulation.
        """
        data = asdict(self)
        # Transform nested FieldDefinition instances into dictionaries.
        data["fields"] = [f.to_dict() for f in self.fields]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchemaDefinition":
        """Construct a :class:`SchemaDefinition` from a dictionary.

        Args:
            data (Dict[str, Any]): Mapping describing the schema.

        Returns:
            SchemaDefinition: Instance populated from ``data``.

        When to use:
            Use when loading schema details from parsed configuration files.
        """
        # Recreate FieldDefinition objects for each nested field mapping.
        fields = [FieldDefinition.from_dict(f) for f in data.get("fields", [])]
        return cls(
            name=data["name"],
            file_path=data.get("file_path"),
            fields=fields,
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        """Serialise the schema definition to JSON.

        Returns:
            str: JSON string representing the schema.

        When to use:
            Use for persisting the schema in JSON format.
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, data: str) -> "SchemaDefinition":
        """Create a :class:`SchemaDefinition` from JSON text.

        Args:
            data (str): JSON representation of the schema.

        Returns:
            SchemaDefinition: Deserialised instance.

        When to use:
            Use when reading a schema definition stored as JSON.
        """
        return cls.from_dict(json.loads(data))

    def to_yaml(self) -> str:
        """Serialise the schema definition to YAML.

        Returns:
            str: YAML string, or JSON if PyYAML isn't installed.

        When to use:
            Preferred for human-readable schema files.
        """
        if yaml:
            return yaml.safe_dump(self.to_dict(), sort_keys=False)
        # Fall back to JSON when PyYAML is unavailable.
        print("PyYAML not installed; using JSON for SchemaDefinition.to_yaml")
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_yaml(cls, data: str) -> "SchemaDefinition":
        """Create a :class:`SchemaDefinition` from YAML text.

        Args:
            data (str): YAML representation (JSON also accepted as fallback).

        Returns:
            SchemaDefinition: Deserialised instance.

        When to use:
            Use for loading schema definitions written in YAML or JSON.
        """
        if yaml:
            raw = yaml.safe_load(data)
        else:
            # Fall back to JSON parsing when the yaml library isn't installed.
            print(
                "PyYAML not installed; parsing SchemaDefinition.from_yaml as JSON"
            )
            raw = json.loads(data)
        return cls.from_dict(raw)


@dataclass
class ProjectConfig:
    """Configuration for a project with source and target schemas."""

    name: str
    target: SchemaDefinition
    sources: List[SchemaDefinition] = field(default_factory=list)
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the project configuration to a dictionary.

        Returns:
            Dict[str, Any]: Mapping with nested schema definitions serialised.

        When to use:
            Use before serialising to JSON/YAML or for programmatic access.
        """
        return {
            "name": self.name,
            "description": self.description,
            # Convert nested schema objects to dictionaries for serialisation.
            "target": self.target.to_dict(),
            "sources": [s.to_dict() for s in self.sources],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectConfig":
        """Construct a :class:`ProjectConfig` from a dictionary.

        Args:
            data (Dict[str, Any]): Mapping describing project settings.

        Returns:
            ProjectConfig: Instance created from ``data``.

        When to use:
            Use when loading project configuration from parsed files.
        """
        # Rebuild nested SchemaDefinition objects from their mappings.
        target = SchemaDefinition.from_dict(data["target"])
        sources = [SchemaDefinition.from_dict(s) for s in data.get("sources", [])]
        return cls(
            name=data["name"],
            target=target,
            sources=sources,
            description=data.get("description"),
        )

    def to_json(self) -> str:
        """Serialise the project configuration to JSON.

        Returns:
            str: JSON representation of the project.

        When to use:
            Use when persisting the configuration in JSON format.
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, data: str) -> "ProjectConfig":
        """Create a :class:`ProjectConfig` from a JSON string.

        Args:
            data (str): JSON text representing the project.

        Returns:
            ProjectConfig: Deserialised instance.

        When to use:
            Use when reading configuration stored as JSON.
        """
        return cls.from_dict(json.loads(data))

    def to_yaml(self) -> str:
        """Serialise the project configuration to YAML.

        Returns:
            str: YAML string; falls back to JSON if PyYAML isn't available.

        When to use:
            Useful for human-editable project configuration files.
        """
        if yaml:
            return yaml.safe_dump(self.to_dict(), sort_keys=False)
        # Fall back to JSON when PyYAML can't be imported.
        print("PyYAML not installed; using JSON for ProjectConfig.to_yaml")
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_yaml(cls, data: str) -> "ProjectConfig":
        """Create a :class:`ProjectConfig` from YAML text.

        Args:
            data (str): YAML representation (JSON also accepted as fallback).

        Returns:
            ProjectConfig: Deserialised configuration instance.

        When to use:
            Use when loading project configuration from YAML or JSON files.
        """
        if yaml:
            raw = yaml.safe_load(data)
        else:
            # Fall back to JSON parsing when PyYAML is missing.
            print(
                "PyYAML not installed; parsing ProjectConfig.from_yaml as JSON"
            )
            raw = json.loads(data)
        return cls.from_dict(raw)
