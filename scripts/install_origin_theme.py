from __future__ import annotations

import argparse
import filecmp
import shutil
from datetime import datetime
from pathlib import Path


DEFAULT_THEME = "写文章专用.oth"


def default_origin_theme_dir() -> Path:
    return Path.home() / "Documents" / "OriginLab" / "User Files" / "Themes" / "Graph"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install bundled Origin graph themes into the Origin user theme directory."
    )
    parser.add_argument(
        "--theme",
        default=DEFAULT_THEME,
        help=f"Bundled theme file name under assets/origin-themes. Default: {DEFAULT_THEME}",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=default_origin_theme_dir(),
        help="Origin graph theme directory. Defaults to Documents/OriginLab/User Files/Themes/Graph.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Overwrite an existing different theme without creating a timestamped backup.",
    )
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    source = skill_dir / "assets" / "origin-themes" / args.theme
    if not source.exists():
        raise SystemExit(f"Theme asset not found: {source}")

    target_dir = args.target_dir.expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name

    if target.exists() and filecmp.cmp(source, target, shallow=False):
        print(f"Already installed: {target}")
        return 0

    if target.exists() and not args.no_backup:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = target.with_name(f"{target.stem}.backup_{stamp}{target.suffix}")
        shutil.copy2(target, backup)
        print(f"Backed up existing theme: {backup}")

    shutil.copy2(source, target)
    print(f"Installed Origin theme: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
