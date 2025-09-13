"""Simple CLI demonstrating error handling."""
from error_handler import DataError, ErrorCollector


def main() -> None:
    collector = ErrorCollector()

    # Example: an incorrect value type
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
