from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument("--app-version", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    bundle_root = Path(args.bundle_root).resolve()
    release_manifest_path = bundle_root / "release-manifest.json"
    engine_manifest_path = bundle_root / "engine" / "manifest.json"

    engine_manifest: dict[str, object] | None = None
    if engine_manifest_path.exists():
        engine_manifest = json.loads(engine_manifest_path.read_text(encoding="utf-8"))

    manifest = {
        "schema": {
            "name": "gprmax-workbench-release-manifest",
            "version": 1,
        },
        "built_at_utc": datetime.now(tz=UTC).isoformat(),
        "app_version": args.app_version,
        "app_source_commit": git_value(repo_root, ["rev-parse", "HEAD"]),
        "app_source_branch": git_value(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"]),
        "bundle_root": bundle_root.name,
        "app_executable": file_record(bundle_root, bundle_root / "GPRMax Workbench.exe"),
        "engine_manifest": engine_manifest,
        "license_inventories": sorted(
            relative_path(path, bundle_root)
            for path in (bundle_root / "licenses").rglob("inventory-*.json")
            if path.is_file()
        ),
        "docs": sorted(
            relative_path(path, bundle_root)
            for path in (bundle_root / "docs").rglob("*.md")
            if path.is_file()
        ),
        "support_assets": sorted(
            relative_path(path, bundle_root)
            for path in (bundle_root / "support").rglob("*")
            if path.is_file()
        ),
    }

    release_manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(release_manifest_path)
    return 0


def file_record(bundle_root: Path, target: Path) -> dict[str, object] | None:
    if not target.exists():
        return None
    return {
        "path": relative_path(target, bundle_root),
        "size_bytes": target.stat().st_size,
    }


def git_value(repo_root: Path, args: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
