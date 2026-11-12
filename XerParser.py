"""Parser for Primavera P6 XER export files.

XER files are tab-delimited exports containing table and field markers:
    %T <table name>
    %F <field 1> <field 2> ...
    %R <value 1> <value 2> ...
    %E

The parser keeps source values as strings. Type conversion and schedule
validation belong in later layers of the application.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ParseIssue:
    """A structural issue found while reading an XER file."""

    line_number: int
    table: str | None
    message: str
    expected_fields: int | None = None
    actual_fields: int | None = None


@dataclass
class XERData:
    """Parsed XER content and any issues encountered during parsing."""

    source: Path
    header: list[str] = field(default_factory=list)
    tables: dict[str, pd.DataFrame] = field(default_factory=dict)
    issues: list[ParseIssue] = field(default_factory=list)

    def get_table(self, table_name: str) -> pd.DataFrame:
        """Return a table, or an empty DataFrame if it is not present."""
        return self.tables.get(table_name.upper(), pd.DataFrame())


def _read_text(path: Path) -> str:
    """Read an XER file using common encodings found in P6 exports."""
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    return path.read_text(encoding="latin-1")


def parse_xer(file_path: str | Path) -> XERData:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"XER file not found: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"Expected an XER file, received a directory: {path}")

    result = XERData(source=path)
    records_by_table: dict[str, list[dict[str, Any]]] = {}
    current_table: str | None = None
    current_fields: list[str] | None = None

    text = _read_text(path)

    try:
        reader = csv.reader(text.splitlines(), delimiter="\t", quoting=csv.QUOTE_NONE)
        for row in reader:
            line_number = reader.line_num
            if not row or not any(value.strip() for value in row):
                continue

            marker = row[0].strip().upper()

            if marker == "ERMHDR":
                result.header = row[1:]
                continue

            if marker == "%T":
                if len(row) < 2 or not row[1].strip():
                    result.issues.append(
                        ParseIssue(line_number, current_table, "Table marker is missing its table name.")
                    )
                    current_table = None
                    current_fields = None
                    continue

                current_table = row[1].strip().upper()
                records_by_table.setdefault(current_table, [])
                current_fields = None
                continue

            if marker == "%F":
                if current_table is None:
                    result.issues.append(
                        ParseIssue(line_number, None, "Field definition found before a table marker.")
                    )
                    continue

                current_fields = [name.strip() for name in row[1:]]
                if not current_fields or any(not name for name in current_fields):
                    result.issues.append(
                        ParseIssue(line_number, current_table, "Field definition contains an empty field name.")
                    )
                if len(set(current_fields)) != len(current_fields):
                    result.issues.append(
                        ParseIssue(line_number, current_table, "Field definition contains duplicate field names.")
                    )
                continue

            if marker == "%R":
                if current_table is None or current_fields is None:
                    result.issues.append(
                        ParseIssue(line_number, current_table, "Data row found without a table and field definition.")
                    )
                    continue

                values = row[1:]
                expected_count = len(current_fields)
                actual_count = len(values)

                if actual_count != expected_count:
                    result.issues.append(
                        ParseIssue(
                            line_number=line_number,
                            table=current_table,
                            message="Data row has a different number of values than its field definition.",
                            expected_fields=expected_count,
                            actual_fields=actual_count,
                        )
                    )

                normalized_values = values[:expected_count]
                normalized_values.extend([""] * (expected_count - len(normalized_values)))
                record = dict(zip(current_fields, normalized_values))
                if actual_count > expected_count:
                    record["_extra_fields"] = values[expected_count:]
                records_by_table[current_table].append(record)
                continue

            if marker == "%E":
                current_table = None
                current_fields = None
                continue

            # Other XER markers/metadata are not table records and are ignored.

    except csv.Error as error:
        result.issues.append(
            ParseIssue(reader.line_num, current_table, f"Unable to parse tab-delimited content: {error}")
        )

    for table_name, records in records_by_table.items():
        result.tables[table_name] = pd.DataFrame(records)

    return result
