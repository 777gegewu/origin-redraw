#!/usr/bin/env python
"""Validate Origin import tables with Origin worksheet label rows.

Expected shape:
    Time    Baseline    Optimized
    h       p.u.        p.u.
            measured    optimized
    0       0.981       1.002
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

def sniff_delimiter(path: Path) -> str:
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:4096]
    if "\t" in sample:
        return "\t"
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        return "\t"


def is_number(value: str) -> bool:
    value = value.strip()
    if value == "":
        return True
    try:
        float(value)
        return True
    except ValueError:
        return False


def validate(path: Path, roles: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"file does not exist: {path}"]
    delim = sniff_delimiter(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=delim))

    if len(rows) < 4:
        return ["table must contain 3 metadata rows plus at least 1 data row"]

    width = len(rows[0])
    if width < 2:
        errors.append("table must contain at least 2 columns")
    for i, row in enumerate(rows, start=1):
        if len(row) != width:
            errors.append(f"row {i} has {len(row)} columns; expected {width}")

    if len(rows) >= 3 and len(rows[2]) == width:
        effective_roles = roles or ["X", *["Y"] * (width - 1)]
        if len(effective_roles) != width:
            errors.append(f"role count {len(effective_roles)} does not match column count {width}")
        else:
            for col_idx, role in enumerate(effective_roles, start=0):
                if role in {"Y", "YErr"}:
                    for row_idx, row in enumerate(rows[3:], start=4):
                        if col_idx >= len(row) or not is_number(row[col_idx]):
                            errors.append(
                                f"row {row_idx} column {col_idx + 1} must be numeric for role {role}"
                            )
                            break

    return errors


def main(argv: list[str]) -> int:
    if len(argv) not in {2, 3}:
        print("usage: validate_origin_table.py <origin_import_table.tsv> [roles_csv]", file=sys.stderr)
        return 2
    path = Path(argv[1])
    roles = [x.strip() for x in argv[2].split(",")] if len(argv) == 3 else None
    errors = validate(path, roles)
    if errors:
        print("INVALID Origin import table:")
        for err in errors:
            print(f"- {err}")
        return 1
    print(f"VALID Origin import table: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
