from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from importlib.metadata import Distribution, distributions
from pathlib import Path

LICENSE_PATTERNS = ("license", "licence", "copying", "notice", "authors")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--scope", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    inventory: list[dict[str, object]] = []
    for distribution_item in distributions():
        inventory.append(export_distribution(distribution_item, output_root))

    inventory.sort(key=lambda item: str(item["name"]).lower())
    inventory_path = output_root / f"inventory-{args.scope}.json"
    inventory_path.write_text(
        json.dumps(
            {
                "schema": {
                    "name": "gprmax-workbench-license-inventory",
                    "version": 1,
                },
                "generated_at_utc": datetime.now(tz=UTC).isoformat(),
                "scope": args.scope,
                "python_version": sys.version.split()[0],
                "distributions": inventory,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(inventory_path)
    return 0


def export_distribution(
    distribution_item: Distribution,
    output_root: Path,
) -> dict[str, object]:
    name = metadata_value(distribution_item, "Name") or "unknown"
    version = metadata_value(distribution_item, "Version") or "unknown"
    license_value = metadata_value(distribution_item, "License-Expression")
    if not license_value:
        license_value = metadata_value(distribution_item, "License")

    copied_files: list[str] = []
    target_root = output_root / safe_name(f"{name}-{version}")
    for source_path in license_files(distribution_item):
        target_root.mkdir(parents=True, exist_ok=True)
        destination = target_root / source_path.name
        destination.write_bytes(source_path.read_bytes())
        copied_files.append(relative_path(destination, output_root))

    return {
        "name": name,
        "version": version,
        "license": license_value,
        "summary": metadata_value(distribution_item, "Summary"),
        "home_page": metadata_value(distribution_item, "Home-page"),
        "license_files": copied_files,
    }


def license_files(distribution_item: Distribution) -> list[Path]:
    matched: dict[str, Path] = {}
    for file_path in distribution_item.files or []:
        filename = Path(str(file_path)).name.lower()
        if not any(pattern in filename for pattern in LICENSE_PATTERNS):
            continue
        resolved = Path(distribution_item.locate_file(file_path))
        if resolved.is_file():
            matched[str(resolved)] = resolved
    return sorted(matched.values(), key=lambda path: path.name.lower())


def metadata_value(distribution_item: Distribution, key: str) -> str | None:
    value = distribution_item.metadata.get(key)
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "distribution"


def relative_path(path: Path, output_root: Path) -> str:
    return path.relative_to(output_root).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
