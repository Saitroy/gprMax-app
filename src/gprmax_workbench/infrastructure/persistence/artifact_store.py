from __future__ import annotations

from pathlib import Path

from ...domain.simulation import RunArtifacts


class RunArtifactStore:
    """Creates run directories and manages input/log/output artifacts."""

    def create_artifacts(self, project_root: Path, run_id: str) -> RunArtifacts:
        run_directory = project_root / "runs" / run_id
        input_directory = run_directory / "input"
        output_directory = run_directory / "output"
        logs_directory = run_directory / "logs"

        for directory in (run_directory, input_directory, output_directory, logs_directory):
            directory.mkdir(parents=True, exist_ok=True)

        return RunArtifacts(
            run_directory=run_directory,
            input_directory=input_directory,
            output_directory=output_directory,
            logs_directory=logs_directory,
            metadata_path=run_directory / "metadata.json",
            input_file=input_directory / "simulation.in",
            stdout_log_path=logs_directory / "stdout.log",
            stderr_log_path=logs_directory / "stderr.log",
            combined_log_path=logs_directory / "combined.log",
        )

    def write_input(self, artifacts: RunArtifacts, input_text: str) -> Path:
        artifacts.input_file.write_text(input_text, encoding="utf-8")
        return artifacts.input_file

    def write_preview(self, project_root: Path, filename: str, input_text: str) -> Path:
        generated_directory = project_root / "generated"
        generated_directory.mkdir(parents=True, exist_ok=True)
        destination = generated_directory / filename
        destination.write_text(input_text, encoding="utf-8")
        return destination

    def export_input(self, destination: Path, input_text: str) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(input_text, encoding="utf-8")
        return destination

    def append_stdout(self, artifacts: RunArtifacts, chunk: str) -> None:
        self._append_text(artifacts.stdout_log_path, chunk)
        self._append_text(artifacts.combined_log_path, f"[stdout] {chunk}")

    def append_stderr(self, artifacts: RunArtifacts, chunk: str) -> None:
        self._append_text(artifacts.stderr_log_path, chunk)
        self._append_text(artifacts.combined_log_path, f"[stderr] {chunk}")

    def list_output_files(self, artifacts: RunArtifacts) -> list[str]:
        if not artifacts.output_directory.exists():
            return []
        output_files: list[str] = []
        for path in sorted(artifacts.output_directory.rglob("*")):
            if path.is_file():
                output_files.append(str(path.relative_to(artifacts.run_directory)))
        return output_files

    def openable_directory(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _append_text(self, path: Path, chunk: str) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(chunk)
