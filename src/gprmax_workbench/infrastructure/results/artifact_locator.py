from __future__ import annotations

import re
from pathlib import Path

from ...domain.results import OutputFileDescriptor, OutputFileKind, RunResultSummary
from ...domain.simulation import SimulationRunRecord

_NATURAL_SORT_RE = re.compile(r"(\d+)")


class ResultArtifactLocator:
    """Finds result artifacts associated with a completed or partial run."""

    def describe_run(self, run_record: SimulationRunRecord) -> RunResultSummary:
        output_files = self._list_output_files(run_record)
        visualisation_artifacts = self._list_visualisation_artifacts(run_record)
        issues: list[str] = []

        if run_record.status.value != "completed":
            issues.append(
                f"Run status is '{run_record.status.value}'. Result files may be incomplete."
            )
        if not output_files:
            issues.append("No .out files were found for this run.")

        return RunResultSummary(
            run_record=run_record,
            output_files=output_files,
            visualisation_artifacts=visualisation_artifacts,
            issues=issues,
        )

    def _list_output_files(
        self,
        run_record: SimulationRunRecord,
    ) -> list[OutputFileDescriptor]:
        candidates: list[Path] = []
        for directory in self._output_directories(run_record):
            candidates.extend(directory.glob("*.out"))

        unique_paths = sorted({path.resolve() for path in candidates}, key=_natural_sort_key)
        descriptors: list[OutputFileDescriptor] = []
        for path in unique_paths:
            descriptors.append(
                OutputFileDescriptor(
                    path=path,
                    name=path.name,
                    kind=self._classify_output_file(path),
                    size_bytes=path.stat().st_size if path.exists() else 0,
                )
            )
        return descriptors

    def _list_visualisation_artifacts(
        self,
        run_record: SimulationRunRecord,
    ) -> list[Path]:
        patterns = ("*.vti", "*.vtp", "*.vtk", "*.png", "*.jpg")
        found: list[Path] = []
        directories = {
            run_record.output_directory,
            run_record.working_directory,
            run_record.input_file.parent,
            run_record.input_file.parent / "output",
        }
        for pattern in patterns:
            for directory in directories:
                if directory.exists():
                    found.extend(directory.glob(pattern))
        return sorted({path.resolve() for path in found}, key=_natural_sort_key)

    def _output_directories(self, run_record: SimulationRunRecord) -> set[Path]:
        return {
            run_record.output_directory,
            run_record.working_directory,
            run_record.input_file.parent / "output",
        }

    def _classify_output_file(self, path: Path) -> OutputFileKind:
        stem = path.stem.lower()
        if stem.endswith("_merged"):
            return OutputFileKind.MERGED
        return OutputFileKind.ASCAN


def _natural_sort_key(path: Path) -> list[object]:
    parts = _NATURAL_SORT_RE.split(path.name.lower())
    values: list[object] = []
    for part in parts:
        if not part:
            continue
        if part.isdigit():
            values.append(int(part))
        else:
            values.append(part)
    return values
