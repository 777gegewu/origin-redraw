# Origin Import Table Format

## Mandatory Interchange Structure

An external `origin导入表.tsv` must contain exactly three metadata rows before data. This is an automation interchange format, not the final visual worksheet layout inside Origin.

1. `Long Name`
2. `Units`
3. `Comments`

These rows become Origin label rows. Do not add an extra first column containing the words `Long Name`, `Units`, or `Comments`. Every row must have the same number of columns.

Example:

```text
Time	Power factor		
h			
	Baseline	Conventional	Optimized
0	0.981	0.990	1.002
1	0.977	0.986	1.005
2	0.984	0.993	1.009
```

For multi-series charts, it is valid to put the shared Y-axis meaning in the first Y column's Long Name and put individual series names in the Comments row, leaving later Long Name cells blank, as Origin-style exported worksheets often do.

## Column Roles

Do not declare plot roles in the third row. The third row is Origin's `Comments` label row.

Declare roles in the JSON graph spec or allow the default first-column-X/rest-Y rule:

- `X`: independent variable or category axis;
- `Y`: plotted value series;
- `YErr`: error bar value;
- `Label`: data label text;
- `Ignore`: imported but not plotted.

Minimum valid plotting table:

- at least one `X`;
- at least one `Y`;
- no blank role for plotted columns;
- every plotted series must have either a Long Name or a Comments entry. For shared-axis multi-series charts, later Y columns may have blank Long Name when the Comments row supplies the series name.

## Origin Worksheet Appearance

After import, Origin should show its native worksheet layout:

- column designation row, for example `A(X)`, `B(Y)`, `C(Y)`;
- label rows such as `长名称`, `单位`, `注释`, `F(x)`, and `迷你图`;
- numeric data beginning below the label rows.

Do not leave the TSV metadata rows as normal data rows inside Origin. The automation script should import a numeric data table, then write Long Name, Units, Comments, and column designations through Origin worksheet properties. `X/Y` role values must become column designations, not Comments text.

## Data Rules

- Keep numeric columns parseable as numbers.
- Category `X` columns may be text.
- Do not mix numbers and units in data cells; put units only in the `Units` row.
- Do not use merged cells.
- Do not duplicate identical Long Name values unless the series is intentionally duplicated and differentiated in Comments.
- Keep source review data and Origin import data separate: `fig_xxx.tsv` for review, `fig_xxx_origin导入表.tsv` for Origin.

## Common Failures

- Only one header row exists.
- The third row is used for `X/Y/Y` roles instead of real comments.
- The role list is written into Origin's `注释` row.
- First column has no `X` role.
- All scenario columns are imported as text.
- Unit strings are embedded in numeric data cells.
- Wide table is used for stacked bars without cumulative or true stacked meaning.
