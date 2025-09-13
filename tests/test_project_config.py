import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from schema_config import FieldDefinition, SchemaDefinition, ProjectConfig


def sample_config() -> ProjectConfig:
    id_field = FieldDefinition(name="id", data_type="integer", validation={"min": 0})
    name_field = FieldDefinition(name="name", data_type="string", required=False)

    source1 = SchemaDefinition(name="source1", file_path="source1.csv", fields=[id_field, name_field])
    source2 = SchemaDefinition(name="source2", file_path="source2.csv", fields=[id_field])
    target = SchemaDefinition(name="target", file_path="target.csv", fields=[id_field, name_field])

    return ProjectConfig(name="project", target=target, sources=[source1, source2])


def test_json_serialization_roundtrip():
    config = sample_config()

    dumped = config.to_json()
    loaded = ProjectConfig.from_json(dumped)

    assert loaded == config


def test_yaml_serialization_roundtrip():
    config = sample_config()

    dumped = config.to_yaml()
    loaded = ProjectConfig.from_yaml(dumped)

    assert loaded == config
