from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--engine-root", required=True)
    parser.add_argument("--app-version", required=True)
    parser.add_argument("--python-executable", required=True)
    parser.add_argument("--gprmax-version", required=True)
    parser.add_argument("--bundle-layout", default="venv")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = Path(args.source_root).resolve()
    engine_root = Path(args.engine_root).resolve()
    engine_root.mkdir(parents=True, exist_ok=True)

    commit = git_value(source_root, ["rev-parse", "HEAD"])
    branch = git_value(source_root, ["rev-parse", "--abbrev-ref", "HEAD"])

    manifest = {
        "schema": {"name": "gprmax-workbench-engine-manifest", "version": 1},
        "built_at_utc": datetime.now(tz=UTC).isoformat(),
        "app_version": args.app_version,
        "engine_version": f"gprmax-{args.gprmax_version}",
        "gprmax_version": args.gprmax_version,
        "gprmax_source_commit": commit,
        "gprmax_source_branch": branch,
        "python_version": sys.version.split()[0],
        "python_executable": args.python_executable,
        "bundle_layout": args.bundle_layout,
        "capabilities": {
            "cpu": "ready",
            "gpu": "optional",
            "mpi": "optional",
        },
        "notes": [
            "Built on a release machine. End users must not compile gprMax manually.",
            "CPU-first baseline bundle. GPU and MPI require separate environment validation.",
        ],
    }

    manifest_path = engine_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(manifest_path)
    return 0


def git_value(source_root: Path, args: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(source_root), *args],
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


if __name__ == "__main__":
    raise SystemExit(main())

