# Origin Redraw JSON Spec

Use this spec with:

```powershell
python %CODEX_HOME%\skills\origin-redraw\scripts\redraw_origin_graphs.py <spec.json>
```

Minimal example:

```json
{
  "export_dir": "exports",
  "project_dir": "origin_projects",
  "export_types": ["png", "emf"],
  "overwrite_existing": true,
  "continue_on_export_error": true,
  "figures": [
    {
      "key": "figure6",
      "origin_table": "data/figure6_origin导入表.tsv",
      "origin_excel": "data/figure6_origin输入表.xlsx",
      "roles": ["X", "Y", "Y"],
      "project_name": "figure6_origin",
      "x_label": "时段 / h",
      "y_label": "功率因数",
      "axis": {
        "y": {"from": 0.9, "to": 1.005, "inc": 0.015}
      },
      "legend_x": 70,
      "legend_y": 10,
      "legend_scale": 50,
      "legend_mode": "comment",
      "legend_visible_only": true,
      "legend_update": "update",
      "legend_overlap_fallback": "increase_y_to",
      "axis_titles_from_long_name": true,
      "dashed_from": 4
    }
  ]
}
```

Fields:

- `export_dir`: output folder for PNG/EMF/PDF, relative to the spec file unless absolute.
- `project_dir`: output folder for `.opju`.
- `export_types`: prefer `["png", "emf"]`; add `pdf` only when needed.
- `overwrite_existing`: delete same-name exports/projects before rerun to avoid Origin overwrite dialogs.
- `continue_on_export_error`: skip failed export commands when possible.
- `figures[].origin_table`: validated table with Long Name, Units, Comments rows.
- `figures[].origin_excel`: optional Excel workbook to import into Origin with `impExcel`; use this when the user provides or expects an Origin-style `.xlsx` input table. When present, the script keeps the workbook's Long Name, Units, and Comments rows and only applies column designations from `roles`.
- `figures[].roles`: Origin plot designations such as `X`, `Y`, `YErr`, `Label`, or `Ignore`. These become column headers like `A(X)` and `B(Y)`; never write them into the table Comments row. If omitted, the script uses first column `X` and all remaining columns `Y`.
- `figures[].axis.x/y`: optional `from`, `to`, `inc`.
- `figures[].axis_titles_from_long_name`: when `true`, uses Origin substitution such as `%(1X,@LA)` and `%(?Y,@LA)` so axis titles come from worksheet Long Name. If omitted, the default is `true` without a theme and `false` with a theme, so saved theme expressions such as `%(?X)` and `%(?Y)` are preserved.
- `figures[].theme`: optional Origin Theme Organizer graph theme name. The script applies it with `themeApply2g theme:="..."`.
- `figures[].legend`: optional boolean; default `true`. The script does not write fixed legend text. It asks Origin to create/update the legend after applying the theme, then runs `legendupdate`.
- `figures[].legend_mode`: default `comment`; passed to Origin `legendupdate` so legend entries come from the worksheet Comments row, matching the usual Theme Organizer setting `@WU: Use Comment (1st line)`.
- `figures[].legend_update`: default `update`; passed to Origin `legendupdate update:=...`. Use `reconstruct` only as a fallback when a theme's saved legend object still truncates entries.
- `figures[].legend_visible_only`: default `true`; passed to Origin `legendupdate hide:=1` to match "show legend for visible plots only".
- `figures[].legend_x/y/scale`: optional legend placement target and font size after update. The current generic script applies `legend_scale` but leaves position to Origin/theme by default; manual or follow-up visual adjustment should move the existing legend object without recreating blank text.
- `figures[].legend_overlap_fallback`: default workflow note, usually `increase_y_to`. After PNG inspection, first move `legend_x/y`; if the legend still covers important curves after reasonable position attempts, increase `axis.y.to` to create headroom and regenerate PNG/EMF.
- `figures[].dashed_from`: first plot index to render as dashed, useful for limits.

Visual QA workflow:

1. Export PNG and inspect it before accepting the figure.
2. If the legend covers data lines or important extrema, adjust `legend_x/y` and rerun.
3. If placement attempts fail, increase `axis.y.to` as the last fallback, then rerun and inspect again.
