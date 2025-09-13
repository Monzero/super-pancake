import os
import sys

import pytest

# Ensure the package root is on the Python path when running tests directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from schema_validator import validate_schema_data


def test_valid_data():
    schema = [
        {"field_name": "id", "data_type": "int64", "primary_key": True, "nullable": False},
        {"field_name": "name", "data_type": "string", "length": 10, "nullable": False},
        {"field_name": "ref_id", "data_type": "int64", "foreign_key_ref": "ref_table"},
    ]
    data = [
        {"id": 1, "name": "Alice", "ref_id": 1},
        {"id": 2, "name": "Bob", "ref_id": 2},
    ]
    fk_reference = {"ref_id": {1, 2}}

    is_valid, errors = validate_schema_data(schema, data, fk_reference)
    assert is_valid
    assert errors == {}


def test_violations():
    schema = [
        {"field_name": "id", "data_type": "int64", "primary_key": True, "nullable": False},
        {"field_name": "name", "data_type": "string", "length": 5, "nullable": False},
        {"field_name": "ref_id", "data_type": "int64", "foreign_key_ref": "ref_table"},
    ]
    data = [
        {"id": 1, "name": "Alice", "ref_id": 3},  # invalid FK
        {"id": 1, "name": "", "ref_id": 1},       # duplicate PK and null name
    ]
    fk_reference = {"ref_id": {1, 2}}

    is_valid, errors = validate_schema_data(schema, data, fk_reference)
    assert not is_valid
    # Ensure all expected keys have violations
    assert set(errors.keys()) == {"id", "name", "ref_id"}
    assert any("Duplicate" in msg for msg in errors["id"])
    assert any("null value" in msg for msg in errors["name"])
    assert any("foreign key" in msg for msg in errors["ref_id"])


def test_source_and_target_use_same_logic():
    source_schema = [
        {"field_name": "id", "data_type": "int64", "primary_key": True, "nullable": False},
        {"field_name": "name", "data_type": "string", "length": 10, "nullable": False},
    ]
    source_data = [
        {"id": 1, "name": "Ann"},
        {"id": 2, "name": "Ben"},
    ]

    target_schema = [
        {"field_name": "id", "data_type": "int64", "primary_key": True, "nullable": False},
        {"field_name": "name", "data_type": "string", "length": 3, "nullable": False},
    ]
    target_data = [
        {"id": 1, "name": "Anna"},  # length exceeds 3
        {"id": 2, "name": "Ben"},
    ]

    assert validate_schema_data(source_schema, source_data)[0]
    is_valid, errors = validate_schema_data(target_schema, target_data)
    assert not is_valid
    assert "name" in errors and any("exceeds" in msg for msg in errors["name"])
