#!/usr/bin/env python
"""Redraw validated Origin import tables through Origin COM.

Usage:
    python redraw_origin_graphs.py spec.json

The spec is intentionally JSON-only so it works on machines without PyYAML.
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import pywintypes

from validate_origin_table import sniff_delimiter, validate


DEFAULT_COLORS = [
    [70, 70, 70],
    [245, 64, 64],
    [30, 115, 220],
    [45, 170, 100],
    [175, 105, 220],
    [220, 145, 35],
]


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def resolve_path(base: Path, value: str | None, default: Path | None = None) -> Path:
    if value:
        path = Path(value)
        if not path.is_absolute():
            path = base / path
        return path.resolve()
    if default is None:
        raise ValueError("path is required")
    return default.resolve()


def labtalk_escape(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', r"\"")


def origin_path(path: Path) -> str:
    return path.resolve().as_posix()


def read_origin_table(path: Path) -> tuple[list[str], list[str], list[str], list[list[str]]]:
    delim = sniff_delimiter(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=delim))
    return rows[0], rows[1], rows[2], rows[3:]


def write_numeric_table(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)


def remove_existing_outputs(
    project_name: str,
    export_dir: Path,
    project_dir: Path,
    export_types: list[str],
    log_path: Path | None,
) -> None:
    for ext in export_types:
        path = export_dir / f"{project_name}.{ext}"
        if path.exists():
            path.unlink()
            log_line(log_path, f"Removed existing export: {path}")
    project_path = project_dir / f"{project_name}.opju"
    if project_path.exists():
        project_path.unlink()
        log_line(log_path, f"Removed existing Origin project: {project_path}")


def log_line(log_path: Path | None, message: str) -> None:
    print(message, flush=True)
    if log_path is not None:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(message + "\n")


def execute(
    origin: Any,
    commands: list[str],
    context: str,
    log_path: Path | None = None,
    continue_on_export_error: bool = False,
) -> None:
    for command in commands:
        log_line(log_path, f"[{context}] {command}")
        try:
            ok = origin.Execute(command)
        except pywintypes.com_error:
            if continue_on_export_error and command.lstrip().startswith("expGraph "):
                log_line(log_path, f"WARN: export command failed and was skipped: {command}")
                continue
            raise
        if not ok:
            if continue_on_export_error and command.lstrip().startswith("expGraph "):
                log_line(log_path, f"WARN: export command returned false and was skipped: {command}")
                continue
            raise RuntimeError(f"Origin command failed for {context}: {command}")


def figure_commands(
    figure: dict[str, Any],
    input_path: Path,
    headers: list[str],
    units: list[str],
    comments: list[str],
    roles: list[str],
    project_name: str,
    export_dir: Path,
    export_types: list[str],
) -> list[str]:
    key = str(figure.get("key") or project_name)
    graph = "".join(ch for ch in key if ch.isascii() and (ch.isalnum() or ch == "_")) or "origin_graph"
    graph = f"{graph}_origin"
    y_indices = [i + 1 for i, role in enumerate(roles) if role == "Y"]
    if not y_indices:
        raise ValueError(f"{key}: at least one Y column is required")

    commands = [
        "doc -s;",
        f'newbook name:="{graph}data" option:=lsname;',
    ]
    is_excel_input = input_path.suffix.lower() in {".xlsx", ".xls", ".xlsm"}
    if is_excel_input:
        desig = "".join(role[0].upper() if role else "N" for role in roles)
        commands.append(
            f'impExcel fname:="{origin_path(input_path)}" firstmode:=0 lname:=1 unit:=2 cmt1:=3 cmt2:=3 desig:="{desig}";'
        )
    else:
        commands.extend(
            [
                f'impASC fname:="{origin_path(input_path)}";',
                "wks.labels(LUC);",
            ]
        )
    for idx, (name, unit, role) in enumerate(zip(headers, units, roles), start=1):
        if role == "X":
            commands.append(f"wks.col{idx}.type=4;")
        elif role == "Y":
            commands.append(f"wks.col{idx}.type=1;")
        if is_excel_input:
            continue
        comment = comments[idx - 1] if idx - 1 < len(comments) else ""
        commands.extend(
            [
                f'wks.col{idx}.lname$="{labtalk_escape(name)}";',
                f'wks.col{idx}.unit$="{labtalk_escape(unit)}";',
                f'wks.col{idx}.comment$="{labtalk_escape(comment)}";',
            ]
        )
    x_index = roles.index("X") + 1
    y_range = f"{min(y_indices)}:{max(y_indices)}"
    plot_type = int(figure.get("plot", 200))
    commands.extend(
        [
            f'plotxy iy:=({x_index},{y_range}) plot:={plot_type} ogl:=[<new name:={graph}>];',
            f"win -a {graph};",
            "layer.unit=0;",
            "layer 76 68 13 15;",
            "layer.x.showGrids=0; layer.y.showGrids=0;",
        ]
    )

    theme = figure.get("theme")
    if theme:
        commands.append(f'themeApply2g theme:="{labtalk_escape(theme)}";')

    axis = figure.get("axis", {})
    for axis_name in ("x", "y"):
        spec = axis.get(axis_name, {})
        if "from" in spec:
            commands.append(f"layer.{axis_name}.from={spec['from']};")
        if "to" in spec:
            commands.append(f"layer.{axis_name}.to={spec['to']};")
        if "inc" in spec:
            commands.append(f"layer.{axis_name}.inc={spec['inc']};")

    if figure.get("style", "zh_submission") == "zh_submission":
        commands.extend(
            [
                "layer.x.showAxes=3; layer.y.showAxes=3;",
                "layer.x.opposite=1; layer.y.opposite=1;",
                "layer.x.showopposite=1; layer.y.showopposite=1;",
                "layer.tickstyle=2; layer.tickL=6; layer.tickW=1.2;",
                "layer.x.ticks=5; layer.y.ticks=5; layer.x2.ticks=0; layer.y2.ticks=0;",
                "layer.x.thickness=1.2; layer.y.thickness=1.2; layer.x2.thickness=1.2; layer.y2.thickness=1.2;",
            ]
        )

    x_label = figure.get("x_label")
    y_label = figure.get("y_label")
    axis_titles_from_long_name = figure.get("axis_titles_from_long_name")
    use_theme_axis_titles = axis_titles_from_long_name is None and bool(theme)
    if axis_titles_from_long_name is None:
        axis_titles_from_long_name = not use_theme_axis_titles
    if axis_titles_from_long_name:
        commands.extend(
            [
                'xb.text$="\\f:宋体(%(1X,@LA))";',
                'yl.text$="\\f:宋体(%(?Y,@LA))";',
            ]
        )
    elif not use_theme_axis_titles:
        if x_label:
            commands.append(f'label -xb "\\f:宋体({labtalk_escape(x_label)})";')
        if y_label:
            commands.append(f'label -yl "\\f:宋体({labtalk_escape(y_label)})";')

    if figure.get("legend", True):
        legend_scale = int(figure.get("legend_scale", 50))
        legend_mode = figure.get("legend_mode", "comment")
        legend_update = figure.get("legend_update", "update")
        visible_only = int(bool(figure.get("legend_visible_only", True)))
        commands.extend(
            [
                "legend;",
                f"legendupdate dest:=layer update:={legend_update} legend:=combine order:=ascend porder:=ascend mode:={legend_mode} hide:={visible_only} fit:=0 indicate:=0;",
                "legend -av;",
                f"legend.fsize={legend_scale};",
            ]
        )

    colors = figure.get("colors", DEFAULT_COLORS)
    origin_color_indices = figure.get("origin_color_indices", [])
    symbols = figure.get("symbols", [])
    symbol_size = figure.get("symbol_size")
    symbol_fill = int(figure.get("symbol_fill", 0))
    symbol_fill_follow_line = bool(figure.get("symbol_fill_follow_line", True))
    line_styles = figure.get("line_styles", [])
    dashed_from = int(figure.get("dashed_from", 4))
    if figure.get("ungroup_plots", bool(symbols or line_styles or origin_color_indices)):
        commands.append("layer -gu;")
    for plot_idx in range(1, len(y_indices) + 1):
        r, g, b = colors[(plot_idx - 1) % len(colors)]
        if origin_color_indices:
            color_value = str(int(origin_color_indices[(plot_idx - 1) % len(origin_color_indices)]))
        else:
            color_value = f"color({r},{g},{b})"
        commands.extend(
            [
                f"range p{plot_idx} = [{graph}]1!{plot_idx};",
                f"set p{plot_idx} -w {figure.get('line_width', 1800)};",
            ]
        )
        if plot_idx <= len(line_styles):
            commands.append(f"set p{plot_idx} -d {int(line_styles[plot_idx - 1])};")
        elif plot_idx >= dashed_from:
            commands.append(f"set p{plot_idx} -d 2;")
        if plot_idx <= len(symbols):
            commands.append(f"set p{plot_idx} -k {int(symbols[plot_idx - 1])};")
            commands.append(f"set p{plot_idx} -kf {symbol_fill};")
        if symbol_size is not None:
            commands.append(f"set p{plot_idx} -z {float(symbol_size)};")
        commands.append(f"set p{plot_idx} -c {color_value};")
        if plot_idx <= len(symbols) and symbol_fill_follow_line:
            commands.append(f"set p{plot_idx} -cse {color_value};")
            commands.append(f"set p{plot_idx} -csf {color_value};")

    for ext in export_types:
        commands.append(
            f'expGraph type:={ext} filename:="{labtalk_escape(project_name)}" path:="{origin_path(export_dir)}";'
        )
    return commands


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        return fail("usage: redraw_origin_graphs.py <spec.json>")
    spec_path = Path(argv[1]).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    base = spec_path.parent
    export_dir = resolve_path(base, spec.get("export_dir"), base / "exports")
    project_dir = resolve_path(base, spec.get("project_dir"), base / "origin_projects")
    log_path = resolve_path(base, spec.get("log_path"), base / "origin_redraw.log")
    log_path.write_text("", encoding="utf-8")
    export_types = spec.get("export_types", ["png", "pdf", "emf"])
    continue_on_export_error = bool(spec.get("continue_on_export_error", True))
    overwrite_existing = bool(spec.get("overwrite_existing", True))
    figures = spec.get("figures", [])
    if not figures:
        return fail("spec must contain a non-empty figures array")

    project_dir.mkdir(parents=True, exist_ok=True)
    export_dir.mkdir(parents=True, exist_ok=True)

    prepared = []
    with tempfile.TemporaryDirectory(prefix="origin_redraw_") as tmp:
        tmp_dir = Path(tmp)
        for figure in figures:
            table = resolve_path(base, figure.get("origin_table"))
            headers, units, comments, rows = read_origin_table(table)
            roles = figure.get("roles") or ["X", *["Y"] * (len(headers) - 1)]
            errors = validate(table, roles)
            if errors:
                print(f"INVALID Origin import table: {table}", file=sys.stderr)
                for err in errors:
                    print(f"- {err}", file=sys.stderr)
                return 1
            log_line(log_path, f"VALID Origin import table: {table}")
            key = str(figure.get("key") or table.stem)
            origin_excel = figure.get("origin_excel")
            if origin_excel:
                input_path = resolve_path(base, origin_excel)
            else:
                input_path = tmp_dir / f"{key}_numeric.tsv"
                write_numeric_table(input_path, headers, rows)
            project_name = str(figure.get("project_name") or key)
            if overwrite_existing:
                remove_existing_outputs(project_name, export_dir, project_dir, export_types, log_path)
            prepared.append((figure, input_path, headers, units, comments, roles, project_name))

        log_line(log_path, "Starting Origin.ApplicationSI ...")
        import win32com.client

        origin = win32com.client.Dispatch("Origin.ApplicationSI")
        log_line(log_path, "Origin COM connected.")
        origin.Visible = bool(spec.get("visible", False))
        try:
            for figure, input_path, headers, units, comments, roles, project_name in prepared:
                origin.NewProject()
                execute(
                    origin,
                    figure_commands(
                        figure,
                        input_path,
                        headers,
                        units,
                        comments,
                        roles,
                        project_name,
                        export_dir,
                        export_types,
                    ),
                    str(figure.get("key") or project_name),
                    log_path,
                    continue_on_export_error,
                )
                project_path = project_dir / f"{project_name}.opju"
                if not origin.Save(str(project_path)):
                    raise RuntimeError(f"Origin project save failed: {project_path}")
                log_line(log_path, f"Saved Origin project: {project_path}")
        finally:
            try:
                origin.Exit()
            except Exception as exc:
                log_line(log_path, f"WARN: Origin exit failed after COM error: {exc}")

    log_line(log_path, f"Exports: {export_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
