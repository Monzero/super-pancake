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
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldDefinition":
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, data: str) -> "FieldDefinition":
        return cls.from_dict(json.loads(data))

    def to_yaml(self) -> str:
        if yaml:
            return yaml.safe_dump(self.to_dict(), sort_keys=False)
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_yaml(cls, data: str) -> "FieldDefinition":
        if yaml:
            raw = yaml.safe_load(data)
        else:
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
        data = asdict(self)
        data["fields"] = [f.to_dict() for f in self.fields]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchemaDefinition":
        fields = [FieldDefinition.from_dict(f) for f in data.get("fields", [])]
        return cls(
            name=data["name"],
            file_path=data.get("file_path"),
            fields=fields,
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, data: str) -> "SchemaDefinition":
        return cls.from_dict(json.loads(data))

    def to_yaml(self) -> str:
        if yaml:
            return yaml.safe_dump(self.to_dict(), sort_keys=False)
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_yaml(cls, data: str) -> "SchemaDefinition":
        if yaml:
            raw = yaml.safe_load(data)
        else:
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
        return {
            "name": self.name,
            "description": self.description,
            "target": self.target.to_dict(),
            "sources": [s.to_dict() for s in self.sources],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectConfig":
        target = SchemaDefinition.from_dict(data["target"])
        sources = [SchemaDefinition.from_dict(s) for s in data.get("sources", [])]
        return cls(
            name=data["name"],
            target=target,
            sources=sources,
            description=data.get("description"),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, data: str) -> "ProjectConfig":
        return cls.from_dict(json.loads(data))

    def to_yaml(self) -> str:
        if yaml:
            return yaml.safe_dump(self.to_dict(), sort_keys=False)
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_yaml(cls, data: str) -> "ProjectConfig":
        if yaml:
            raw = yaml.safe_load(data)
        else:
            raw = json.loads(data)
        return cls.from_dict(raw)
