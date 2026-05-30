---
name: origin-redraw
description: Extract figure data, build and validate Origin import tables, and automate publication-style Origin redraws. Use when Codex needs to redraw charts from PDFs/images/data into Origin, generate `origin导入表.tsv`, call Origin, export OPJ/OPJU plus EMF/PDF/PNG, or fix recurring Origin data-import format errors.
---

# Origin Redraw

## Core Rule

Do not call Origin until the import table and graph spec pass validation. Most failures in this workflow come from malformed `origin导入表.tsv`, missing Long Name/Units/Comments rows, wrong X/Y column roles in the JSON spec, or data arranged in a chart-incompatible shape.

## Workflow

1. Identify the figure type and data source:
   - direct table data from source files;
   - extracted curve/bar data from PDF or image;
   - reconstructed demonstration data when the user explicitly accepts semi-theoretical reconstruction.
2. Create two data files:
   - ordinary `fig_xxx.tsv` or `fig_xxx.csv` for review;
   - Origin import table `fig_xxx_origin导入表.tsv`.
3. Validate the Origin import table before opening Origin:
   ```powershell
   python %CODEX_HOME%\skills\origin-redraw\scripts\validate_origin_table.py <origin导入表.tsv>
   ```
4. If validation fails, fix the table first. Do not proceed to Origin.
5. Create or update an Origin project only after validation passes.
6. Prefer the bundled automation script instead of writing one-off project COM scripts:
   ```powershell
   python %CODEX_HOME%\skills\origin-redraw\scripts\redraw_origin_graphs.py <spec.json>
   ```
   The project should provide data/config only; the Origin COM workflow should stay in this skill unless a task has a genuinely unique plot type.
7. Write worksheet metadata inside Origin as Long Name, Units, and Comments; do not rely only on external TSV headers.
8. Export checked outputs:
   - `OPJU/OPJ` source project;
   - `EMF` for Word when possible;
   - `PDF` or `PNG` for review.
9. Verify exported figure:
   - file exists and is nonzero;
   - axes, legend, labels, units, curves/bars are visible;
   - data point or category count matches input table;
   - Chinese text and English acronyms render correctly.

## Required Interchange Table Format

Read `references/origin-table-format.md` when creating or debugging `origin导入表.tsv`.

Minimum rule: the external `origin导入表.tsv` must use three metadata rows before numeric data. This is an interchange format for automation, not the final worksheet appearance inside Origin.

```text
时间<TAB>功率因数<TAB><TAB>
h<TAB><TAB><TAB>
<TAB>基准方式<TAB>常规控制<TAB>自动优化控制
1<TAB>0.922<TAB>0.942<TAB>0.985
2<TAB>0.926<TAB>0.947<TAB>0.986
```

Use the third row for real Origin comments. Do not write `X/Y/Y` in the Comments row. Column roles belong in the JSON spec as `roles`, or default to first column `X` and remaining columns `Y`.

For multi-series charts sharing one Y-axis meaning, put the shared Y-axis meaning in the first Y column's Long Name and put series names in the Comments row. Later Y-column Long Name cells may be blank when their series name is supplied in Comments.

Inside Origin, the worksheet should look like the native layout: column headers such as `A(X)`, `B(Y)`, then label rows such as `长名称`, `单位`, `注释`, `F(x)`, and `迷你图`, followed by numeric data. Do not leave the three TSV metadata rows as ordinary data rows in Origin.

## Chart-Type Selection

- Time series or ordered samples: one `X` column plus one or more `Y` columns.
- Category comparison: first column is `X` category labels; subsequent columns are `Y`.
- Multi-scenario grouped bars: wide table with category `X` and scenario `Y` columns.
- Stacked contribution bars: use cumulative-boundary or true stacked-bar data, not manually overlaid image segments.
- Scatter: one `X` and one `Y` per series; use additional columns only when their role is explicit.

For detailed chart rules, read `references/chart-type-rules.md`.

## Origin Automation Constraints

- Apply the project or workspace theme when available; if unavailable, reproduce the equivalent font, line width, color, and axis style manually.
- Chinese text should use Songti; English text and acronyms should use Times New Roman where journal-style output is required.
- Do not use Origin default styling as final output unless the user explicitly accepts it.
- Chinese-submission graph defaults: keep four-side borders, use inward ticks only on bottom and left axes, and remove top/right ticks.
- Axis titles default to worksheet Long Name substitution only when no graph theme is applied. When `theme` is set, let the theme's own axis-title expressions such as `%(?X)` and `%(?Y)` remain in control unless the task spec explicitly sets `axis_titles_from_long_name: true`.
- For point-line figures, use an Origin line+symbol plot type through `figures[].plot`, then set per-curve symbols with `figures[].symbols` and optional `figures[].symbol_size`. Do not rely on a screenshot-only redraw where all points share the same symbol.
- For line styles, prefer explicit `figures[].line_styles` when individual curves need specific solid/dashed patterns. Use `dashed_from` only as a simple shorthand for limit/reference curves.
- Legend placement must be verified from exported PNG screenshots. If the legend overlaps data curves, first try moving only the legend (`legend_x`, `legend_y`) and keep the theme/text style intact. If reasonable legend-position attempts still fail, increase the Y-axis maximum (`axis.y.to`) as the fallback, then re-export PNG/EMF and re-check.
- Saved graph themes from Origin Theme Organizer can be applied by name with `themeApply2g theme:="Theme Name"`. Use this only when the user provides the exact theme name or the task spec contains `theme`.
- Treat Origin COM as unstable: set a task-level timeout, keep logs, and preserve validated data tables before any automated run.
- When rerunning into the same output folder, delete same-name exports before `expGraph`; this avoids Origin hanging on overwrite prompts.
- Prefer `PNG + EMF` for automated runs. Add `PDF` only when specifically needed, because some Origin COM sessions fail or hang on PDF export.
- If Origin fails or hangs, report the failure and keep the validated table; any fallback figure must be marked as non-Origin output.

## Generic Redraw Script

Use `scripts/redraw_origin_graphs.py` with a JSON spec. Read `references/origin-redraw-spec.md` when building or debugging the spec.

The script:

- validates every `origin导入表.tsv`;
- imports data into Origin from `origin_excel` with `impExcel` when provided, otherwise from a temporary numeric TSV;
- when `origin_excel` is provided, treat its first three rows as the Origin worksheet label rows and do not overwrite Long Name, Units, or Comments after import;
- when TSV is used, writes Long Name, Units, and Comments into the Origin worksheet and writes `roles` separately as column designations;
- applies Chinese-submission defaults: four-side axes, inward ticks, no grid, Songti axis label font, while preserving theme-controlled axis titles when a theme is used;
- after applying a theme, asks Origin to create/update the legend with `legend;` and then updates it with `legendupdate` from the worksheet Comments row instead of writing fixed legend text; use reconstruction only as an explicit fallback when update cannot add all visible plots;
- removes same-name exports/projects before rerun when `overwrite_existing` is true;
- writes `origin_redraw.log` beside the spec.

After export, inspect the PNG visually before accepting the result. Check at minimum:

- legend row count matches visible plot count;
- legend does not cover data lines, markers, axis titles, tick labels, or important curve extrema;
- top/right borders have no ticks and bottom/left ticks point inward;
- axis titles and legend labels use the expected worksheet metadata.

If legend overlap is detected, iterate in this order:

1. Move the legend within the plot area using `legend_x` and `legend_y`.
2. If no clean in-plot location exists, move the legend just outside the data-dense region while preserving readability.
3. If those attempts still fail, increase `axis.y.to` enough to create headroom, keep the original `axis.y.from` unless there is a clear reason to change it, and regenerate both PNG and EMF.

## Deliverable Checklist

Report these items in the final response:

- source data path;
- validated `origin导入表.tsv` path;
- Origin project path, if generated;
- exported EMF/PDF/PNG paths;
- validation status;
- any remaining non-Origin or format risks.
