"""Schema definition models with identifiers for profiler integration.

Each table and field is assigned a stable ``id`` value so that profiling
results can be associated back to the original schema definition.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class FieldSchema:
    """Metadata describing a field within a table."""

    id: str
    name: str
    data_type: str = ""
    description: str = ""
    nullable: bool = True


@dataclass
class TableSchema:
    """Collection of fields describing a table."""

    id: str
    name: str
    fields: List[FieldSchema] = field(default_factory=list)
