"""Validation logic for schemas and sample data."""
from __future__ import annotations
from typing import Any, Dict, List, Tuple, Optional, Set
import logging


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when critical mismatches are found during validation."""


def _is_null(value: Any) -> bool:
    """Return True if value should be considered null."""
    return value is None or (isinstance(value, str) and value == "")


def _check_type(value: Any, expected_type: str) -> bool:
    """Validate a single value against an expected type."""
    if _is_null(value):
        return True  # Nullability handled separately

    expected_type = expected_type.lower()
    try:
        if expected_type.startswith("int"):
            int(value)
        elif expected_type.startswith("float"):
            float(value)
        elif expected_type in {"string", "str"}:
            str(value)
        else:
            return False
    except (ValueError, TypeError):
        return False
    return True


def validate_schema_data(
    schema: List[Dict[str, Any]],
    data: List[Dict[str, Any]],
    fk_reference: Optional[Dict[str, Set[Any]]] = None,
) -> Tuple[bool, Dict[str, List[str]]]:
    """Validate sample data against a schema.

    Parameters
    ----------
    schema:
        List of field definitions. Each definition should contain at least
        ``field_name`` and ``data_type``. Optional keys include ``length``,
        ``nullable`` (bool), ``primary_key`` (bool) and ``foreign_key_ref``.
    data:
        Sample data represented as a list of dictionaries mapping field names to
        values.
    fk_reference:
        Optional mapping of field name to a set of allowed values for foreign
        key validation.

    Returns
    -------
    Tuple of ``(is_valid, errors)`` where ``is_valid`` indicates whether the
    sample data satisfies all constraints and ``errors`` maps field names to a
    list of human readable violation messages.

    Any violation results in ``is_valid`` being ``False``. Callers should block
    project save when ``is_valid`` is ``False``.
    """

    fk_reference = fk_reference or {}
    errors: Dict[str, List[str]] = {}

    # Stage 1: Precompute column values for efficiency.
    column_values: Dict[str, List[Any]] = {name: [] for name in [f["field_name"] for f in schema]}
    for row in data:
        for name in column_values:
            column_values[name].append(row.get(name))
    logger.debug(
        "Precomputed column values for %d fields across %d rows",
        len(column_values),
        len(data),
    )

    # Stage 2: Iterate through each field performing validation checks.
    for field in schema:
        name = field["field_name"]
        expected_type = field.get("data_type", "string")
        length = field.get("length")
        nullable = field.get("nullable", True)
        is_primary = bool(field.get("primary_key"))
        fk_ref = field.get("foreign_key_ref")
        field_errors: List[str] = []

        values = column_values[name]
        logger.debug("Validating field '%s'", name)

        # Validate individual values (type, nullability, length)
        for i, value in enumerate(values):
            if not _check_type(value, expected_type):
                field_errors.append(f"Row {i}: value {value!r} does not match type {expected_type}")
            if not nullable and _is_null(value):
                field_errors.append(f"Row {i}: null value in non-nullable field")
            if isinstance(value, str) and length and len(value) > int(length):
                field_errors.append(
                    f"Row {i}: value {value!r} exceeds max length {length}"
                )

        # Stage 3: Constraint enforcement
        # Primary key constraint: uniqueness and non-null
        if is_primary:
            non_null_values = [v for v in values if not _is_null(v)]
            if len(non_null_values) != len(set(non_null_values)):
                field_errors.append("Duplicate values in primary key column")
            if any(_is_null(v) for v in values):
                field_errors.append("Null value in primary key column")

        # Foreign key constraint
        if fk_ref:
            allowed = fk_reference.get(name, set())
            for i, value in enumerate(values):
                if not _is_null(value) and value not in allowed:
                    field_errors.append(
                        f"Row {i}: value {value!r} not present in foreign key reference"
                    )
        if field_errors:
            logger.debug(
                "Field '%s' failed validation with %d error(s)",
                name,
                len(field_errors),
            )
            errors[name] = field_errors
        else:
            logger.debug("Field '%s' passed validation", name)

    is_valid = not errors
    if is_valid:
        logger.info("Schema data validation completed successfully")
    else:
        logger.info(
            "Schema data validation found errors in %d field(s)",
            len(errors),
        )
    return is_valid, errors
