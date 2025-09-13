"""Project configuration models for the data profiler.

These data classes define placeholders for profiler output so that
future components can persist metrics without changing the overall
configuration structure.

Extension points
----------------
``ProjectConfig.field_profiles`` and ``ProjectConfig.table_profiles``
are intentionally open ended. They are mappings keyed by field or
table identifier and each profile exposes a ``statistics`` mapping that
can accept any key/value pair. As additional profiler metrics are
implemented, they can be stored here without modifying existing code.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class FieldProfile:
    """Stores profiling statistics for a single field."""

    field_id: str
    statistics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TableProfile:
    """Stores profiling statistics for a table."""

    table_id: str
    statistics: Dict[str, Any] = field(default_factory=dict)
    field_profiles: Dict[str, FieldProfile] = field(default_factory=dict)


@dataclass
class ProjectConfig:
    """Top-level project configuration including profiler results."""

    project_name: str
    table_profiles: Dict[str, TableProfile] = field(default_factory=dict)
    field_profiles: Dict[str, FieldProfile] = field(default_factory=dict)
