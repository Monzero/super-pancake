"""Simple CLI demonstrating error handling.

Run this module to see how an :class:`ErrorCollector` aggregates
validation problems. The script creates a sample :class:`DataError` and
prints a formatted summary to the console, illustrating how errors might be
reported in a data processing pipeline.
"""
from error_handler import DataError, ErrorCollector


def main() -> None:
    """Execute the demo workflow.

    A new :class:`ErrorCollector` is created, an example ``DataError`` is
    registered, and the collected issues are displayed. This mirrors the
    basic flow of validating input data and presenting any problems that were
    found.
    """
    collector = ErrorCollector()

    # Simulate validation failure for an "age" field where a string was
    # provided instead of the expected integer. The collector records this
    # issue so it can be displayed later.
    collector.add_error(
        DataError(
            field_name="age",
            row_number=5,
            message="expected int64 but got string",
            suggestion="Convert value to integer",
        )
    )

    collector.display()


if __name__ == "__main__":
    main()
