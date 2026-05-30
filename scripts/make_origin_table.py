#!/usr/bin/env python
"""Create a simple Origin import table from a CSV/TSV file."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def sniff_delimiter(path: Path) -> str:
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:4096]
    if "\t" in sample:
        return "\t"
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
    except csv.Error:
        return ","


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--units", default="", help="comma-separated units, optional")
    parser.add_argument("--comments", default="", help="comma-separated comments, optional")
    parser.add_argument("--has-header", action="store_true")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    delim = sniff_delimiter(src)
    rows = list(csv.reader(src.open("r", encoding="utf-8-sig", newline=""), delimiter=delim))
    if not rows:
        raise SystemExit("input is empty")

    if args.has_header:
        long_names = [x.strip() for x in rows[0]]
        data = rows[1:]
    else:
        long_names = [f"Column {i + 1}" for i in range(len(rows[0]))]
        data = rows

    units = [x.strip() for x in args.units.split(",")] if args.units else [""] * len(long_names)
    comments = [x.strip() for x in args.comments.split(",")] if args.comments else [""] * len(long_names)
    if len(units) < len(long_names):
        units += [""] * (len(long_names) - len(units))
    if len(comments) < len(long_names):
        comments += [""] * (len(long_names) - len(comments))

    out_rows = [
        long_names,
        units[: len(long_names)],
        comments[: len(long_names)],
        *data,
    ]
    with dst.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerows(out_rows)
    print(dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
