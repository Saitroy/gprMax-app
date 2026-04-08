from __future__ import annotations

import argparse
import json
import os
import platform
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_APP_NAME = "gprmax_workbench"


@dataclass(frozen=True, slots=True)
class BundleEntry:
    source: Path
    archive_name: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-name", default=DEFAULT_APP_NAME)
    parser.add_argument("--settings-root")
    parser.add_argument("--project-root")
    parser.add_argument("--run-id")
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings_root = (
        Path(args.settings_root).expanduser().resolve()
        if args.settings_root
        else default_settings_dir(args.app_name)
    )
    project_root = (
        Path(args.project_root).expanduser().resolve()
        if args.project_root
        else None
    )

    entries, selected_run_id = collect_entries(
        settings_root=settings_root,
        project_root=project_root,
        run_id=args.run_id,
    )
    output_path = resolve_output_path(args.output)

    manifest = {
        "schema": {
            "name": "gprmax-workbench-support-bundle",
            "version": 1,
        },
        "created_at_utc": datetime.now(tz=UTC).isoformat(),
        "platform": platform.platform(),
        "settings_root": str(settings_root),
        "project_root": str(project_root) if project_root is not None else None,
        "selected_run_id": selected_run_id,
        "files": [entry.archive_name for entry in entries],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "support_manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False),
        )
        for entry in entries:
            archive.write(entry.source, entry.archive_name)

    print(output_path)
    return 0


def resolve_output_path(output_value: str | None) -> Path:
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    default_name = f"support-bundle-{timestamp}.zip"
    if not output_value:
        return Path.cwd() / default_name
    output_path = Path(output_value).expanduser().resolve()
    if output_path.suffix.lower() == ".zip":
        return output_path
    return output_path / default_name


def collect_entries(
    *,
    settings_root: Path,
    project_root: Path | None,
    run_id: str | None,
) -> tuple[list[BundleEntry], str | None]:
    entries: list[BundleEntry] = []
    add_file(entries, settings_root / "settings.json", "app/settings.json")
    add_tree(entries, settings_root / "logs", "app/logs")

    selected_run_id: str | None = None
    if project_root is not None:
        add_file(entries, project_root / "project.gprwb.json", "project/project.gprwb.json")
        run_dir = resolve_run_dir(project_root, run_id)
        if run_dir is not None:
            selected_run_id = run_dir.name
            add_file(entries, run_dir / "metadata.json", f"project/runs/{run_dir.name}/metadata.json")
            add_tree(entries, run_dir / "logs", f"project/runs/{run_dir.name}/logs")
            add_tree(entries, run_dir / "input", f"project/runs/{run_dir.name}/input")

    return entries, selected_run_id


def resolve_run_dir(project_root: Path, run_id: str | None) -> Path | None:
    runs_root = project_root / "runs"
    if not runs_root.exists():
        return None
    if run_id:
        candidate = runs_root / run_id
        return candidate if candidate.is_dir() else None

    candidates = [path for path in runs_root.iterdir() if path.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, path.name))


def add_file(entries: list[BundleEntry], source: Path, archive_name: str) -> None:
    if source.is_file():
        entries.append(BundleEntry(source=source, archive_name=archive_name))


def add_tree(entries: list[BundleEntry], source_root: Path, archive_root: str) -> None:
    if not source_root.is_dir():
        return
    for source_path in sorted(source_root.rglob("*")):
        if source_path.is_file():
            relative = source_path.relative_to(source_root).as_posix()
            entries.append(
                BundleEntry(
                    source=source_path,
                    archive_name=f"{archive_root}/{relative}",
                )
            )


def default_settings_dir(app_name: str) -> Path:
    system = platform.system()
    if system == "Windows":
        root = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return root / app_name
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / app_name
    return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / app_name


if __name__ == "__main__":
    raise SystemExit(main())
