"""Utilities for representing and collecting data validation errors.

This module exposes two main classes:

* ``DataError`` -- describes validation problems for specific fields and
  rows within a dataset.
* ``ErrorCollector`` -- aggregates ``DataError`` instances and logs or
  displays them.

Inputs handled by this module include ``DataError`` objects providing
field names, optional row numbers, error messages and suggestions, and an
optional ``log_file`` path when instantiating ``ErrorCollector``.
"""

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
        """Return human-readable description of the error.

        Builds a message including the field name, optional row number, and
        any suggestion for resolving the issue.
        """

        # Begin constructing the base message with the field information.
        base = f"{self.message} (field: {self.field_name}"

        # Include row number when it is provided.
        if self.row_number is not None:
            base += f", row: {self.row_number}"

        # Close the parenthetical started above.
        base += ")"

        # Append suggestion details if available.
        if self.suggestion:
            base += f" Suggestion: {self.suggestion}"

        return base


class ErrorCollector:
    """Collects ``DataError`` objects and handles logging and display."""

    def __init__(self, log_file: str = "errors.log") -> None:
        """Create a new collector for ``DataError`` objects.

        Parameters
        ----------
        log_file:
            Path to the file where error messages will be written.

        Behavior
        --------
        Sets up logging and prepares an internal list for storing errors.
        """

        # Prepare container for error instances.
        self.errors: List[DataError] = []

        # Configure the logger to write error details to ``log_file``.
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(message)s",
        )
        self.logger = logging.getLogger("data_error_logger")

        # Provide immediate feedback that the collector is initialized.
        print(f"ErrorCollector initialized, logging to {log_file}")

    def add_error(self, error: DataError) -> None:
        """Add an error to the collection and persist it to the log."""

        # Store the error in the internal list.
        self.errors.append(error)

        # Log the error message to the configured logger.
        self.logger.info(str(error))

        # Indicate via stdout that an error has been recorded.
        print(f"Error added: {error}")

    def display(self) -> None:
        """Display collected errors to the console."""

        # Announce that errors are about to be shown.
        print("Displaying collected errors:")

        # Iterate through stored errors and print each one.
        for err in self.errors:
            print(str(err))
