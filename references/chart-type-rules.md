# Chart-Type Rules

## Line Chart

Use for time series, voltage curves, power-factor curves, iteration curves, loss curves, and forecast comparisons.

Required shape:

```text
Time	Method A	Method B
h	p.u.	p.u.
X	Y	Y
...
```

## Grouped Bar Chart

Use for scenario comparisons or algorithm metrics.

Required shape:

```text
Scenario	Baseline	Conventional	Proposed
	%	%	%
X	Y	Y	Y
...
```

## Stacked Bar Chart

Use only when columns are parts of the same total. Do not use stacked bars for unrelated indicators.

Required shape:

```text
Scenario	Source A	Source B	Source C
	Mvar	Mvar	Mvar
X	Y	Y	Y
...
```

## Scatter Chart

Use when both axes are measured variables.

Required shape:

```text
Active Power	Reactive Power
MW	Mvar
X	Y
...
```

## Heatmap or Matrix

Use only when the data is truly two-dimensional. Keep a review copy and document how rows and columns map to axes.

## Selection Guardrail

If the chart type is uncertain, first produce the review TSV and a short note explaining candidate chart types. Do not guess silently and create an Origin project with the wrong data shape.
