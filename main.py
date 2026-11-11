
import argparse
from pathlib import Path

from XerParser import parse_xer
from XerValidator import validate_xer
from XerChartGenerator import generate_chart


def main():
    """Parse, validate, and visualize an XER file."""

    argument_parser = argparse.ArgumentParser(
        description="Primavera P6 XER Schedule Checker"
    )

    argument_parser.add_argument(
        "file_path",
        help="Path to the XER file"
    )

    args = argument_parser.parse_args()
    file_path = Path(args.file_path)

    # 1. Parse the XER file.
    print(f"\nReading XER file: {file_path}")

    xer_data = parse_xer(file_path)

    print(f"Parser issues: {len(xer_data.issues)}")

    # Display parser issues, if any.
    for issue in xer_data.issues:
        print(
            f"Line {issue.line_number}: {issue.message}"
        )

    # 2. Validate the parsed XER data.
    validation_result = validate_xer(xer_data)

    # 3. Display validation summary.
    print("\nSCHEDULE VALIDATION RESULTS")
    print("=" * 40)

    missing_links_count = len(
        validation_result["missing_links"]
    )

    negative_float_count = len(
        validation_result["negative_float"]
    )

    high_float_count = len(
        validation_result["high_float"]
    )

    print(f"Missing Links: {missing_links_count}")
    print(f"Negative Float: {negative_float_count}")
    print(f"High Float: {high_float_count}")

    # 4. Display detailed findings.
    for category, dataframe in validation_result.items():

        print(f"\n{category.upper()}")
        print("-" * 40)

        if dataframe.empty:
            print("No findings.")
            continue

        display_columns = [
            column for column in [
                "task_id",
                "task_code",
                "task_name",
                "total_float_hr_cnt",
                "missing_type"
            ]
            if column in dataframe.columns
        ]

        print(
            dataframe[display_columns].to_string(index=False)
        )

    # 5. Generate chart.
    generate_chart(
        missing_links_count,
        negative_float_count,
        high_float_count,
        file_path.stem
    )


if __name__ == "__main__":
    main()
