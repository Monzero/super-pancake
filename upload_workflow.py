"""Simple upload workflow integrating workbook validation."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from workbook_validator import WorkbookValidationError, validate_workbook


def upload_workbook(path: str | Path) -> Dict[str, Any]:
    """Process an uploaded workbook located at *path*.

    Returns a dictionary describing the outcome. Invalid workbooks are rejected
    with a descriptive error message, while valid workbooks return a success
    status. In a real application this is where the workbook would be persisted
    or further processed.
    """
    try:
        validate_workbook(str(path))
    except WorkbookValidationError as exc:
        return {"status": "error", "error": str(exc)}

    # Placeholder for additional processing of the workbook.
    return {"status": "ok"}
