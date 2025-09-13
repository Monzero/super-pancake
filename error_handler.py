from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import logging


@dataclass
class DataError:
    """Represent a validation error for a specific field."""
    field_name: str
    row_number: Optional[int]
    message: str
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        base = f"{self.message} (field: {self.field_name}"
        if self.row_number is not None:
            base += f", row: {self.row_number}"
        base += ")"
        if self.suggestion:
            base += f" Suggestion: {self.suggestion}"
        return base


class ErrorCollector:
    """Collects DataError objects and handles logging/display."""

    def __init__(self, log_file: str = "errors.log") -> None:
        self.errors: List[DataError] = []
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(message)s",
        )
        self.logger = logging.getLogger("data_error_logger")

    def add_error(self, error: DataError) -> None:
        """Add an error to the collection and persist it to the log."""
        self.errors.append(error)
        self.logger.info(str(error))

    def display(self) -> None:
        """Display collected errors to the console."""
        for err in self.errors:
            print(str(err))
