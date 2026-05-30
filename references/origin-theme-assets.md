# Bundled Origin Theme Assets

This skill bundles Origin graph themes that are required for reproducible redraws.

## Bundled Themes

- `assets/origin-themes/写文章专用.oth`
  - Use with JSON field `"theme": "写文章专用"`.
  - For line+symbol plots where this theme already gives acceptable curve colors, symbols, and line styles, set `"theme_controls_series": true`.
  - Then the redraw script should only adjust axis ranges, legend refresh, and export settings.

## Install

Install bundled themes into the current Windows user's Origin graph theme directory:

```powershell
python %CODEX_HOME%\skills\origin-redraw\scripts\install_origin_theme.py
```

The default target is:

```text
%USERPROFILE%\Documents\OriginLab\User Files\Themes\Graph
```

If a different theme with the same file name already exists, the installer creates a timestamped `.backup_YYYYMMDD_HHMMSS.oth` beside it before overwriting.

Use `--target-dir` when Origin's user files are stored elsewhere:

```powershell
python %CODEX_HOME%\skills\origin-redraw\scripts\install_origin_theme.py --target-dir "D:\OriginLab\User Files\Themes\Graph"
```

## Redraw Rule

Prefer theme-owned styling when a saved Origin theme exists. Do not manually set per-curve colors, symbols, or line styles unless the exported PNG shows that the theme result is wrong.
