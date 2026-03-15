from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ...domain.execution_status import SimulationMode, SimulationStatus
from ...domain.gprmax_config import SimulationRunConfig
from ...domain.simulation import RUN_SCHEMA_NAME, RUN_SCHEMA_VERSION, SimulationRunRecord


class RunRepository:
    """Stores and loads per-run metadata manifests."""

    def save(self, run_record: SimulationRunRecord) -> Path:
        payload = {
            "schema": {
                "name": RUN_SCHEMA_NAME,
                "version": RUN_SCHEMA_VERSION,
            },
            "run_id": run_record.run_id,
            "project_root": str(run_record.project_root),
            "project_name": run_record.project_name,
            "status": run_record.status.value,
            "created_at": run_record.created_at.isoformat(),
            "started_at": _serialize_datetime(run_record.started_at),
            "finished_at": _serialize_datetime(run_record.finished_at),
            "working_directory": str(run_record.working_directory),
            "input_file": str(run_record.input_file),
            "output_directory": str(run_record.output_directory),
            "stdout_log_path": str(run_record.stdout_log_path),
            "stderr_log_path": str(run_record.stderr_log_path),
            "combined_log_path": str(run_record.combined_log_path),
            "metadata_path": str(run_record.metadata_path),
            "command": list(run_record.command),
            "exit_code": run_record.exit_code,
            "error_summary": run_record.error_summary,
            "output_files": list(run_record.output_files),
            "configuration": {
                "mode": run_record.configuration.mode.value,
                "use_gpu": run_record.configuration.use_gpu,
                "gpu_device_ids": list(run_record.configuration.gpu_device_ids),
                "benchmark": run_record.configuration.benchmark,
                "geometry_fixed": run_record.configuration.geometry_fixed,
                "write_processed": run_record.configuration.write_processed,
                "num_model_runs": run_record.configuration.num_model_runs,
                "restart_from_model": run_record.configuration.restart_from_model,
                "mpi_tasks": run_record.configuration.mpi_tasks,
                "mpi_no_spawn": run_record.configuration.mpi_no_spawn,
                "extra_arguments": list(run_record.configuration.extra_arguments),
            },
        }
        run_record.metadata_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return run_record.metadata_path

    def load_history(self, project_root: Path) -> list[SimulationRunRecord]:
        runs_directory = project_root / "runs"
        if not runs_directory.exists():
            return []

        history: list[SimulationRunRecord] = []
        for metadata_path in sorted(runs_directory.glob("*/metadata.json"), reverse=True):
            history.append(self.load(metadata_path))
        history.sort(key=lambda item: item.created_at, reverse=True)
        return history

    def load(self, metadata_path: Path) -> SimulationRunRecord:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        configuration_payload = payload.get("configuration", {})
        return SimulationRunRecord(
            run_id=str(payload["run_id"]),
            project_root=Path(payload["project_root"]),
            project_name=str(payload.get("project_name", "")),
            status=SimulationStatus(payload["status"]),
            created_at=_deserialize_datetime(payload["created_at"]),
            started_at=_deserialize_datetime(payload.get("started_at")),
            finished_at=_deserialize_datetime(payload.get("finished_at")),
            working_directory=Path(payload["working_directory"]),
            input_file=Path(payload["input_file"]),
            output_directory=Path(payload["output_directory"]),
            stdout_log_path=Path(payload["stdout_log_path"]),
            stderr_log_path=Path(payload["stderr_log_path"]),
            combined_log_path=Path(payload["combined_log_path"]),
            metadata_path=Path(payload["metadata_path"]),
            command=[str(item) for item in payload.get("command", [])],
            exit_code=payload.get("exit_code"),
            error_summary=str(payload.get("error_summary", "")),
            output_files=[str(item) for item in payload.get("output_files", [])],
            configuration=SimulationRunConfig(
                mode=SimulationMode(configuration_payload.get("mode", "normal")),
                use_gpu=bool(configuration_payload.get("use_gpu", False)),
                gpu_device_ids=[
                    int(item) for item in configuration_payload.get("gpu_device_ids", [])
                ],
                benchmark=bool(configuration_payload.get("benchmark", False)),
                geometry_fixed=bool(configuration_payload.get("geometry_fixed", False)),
                write_processed=bool(configuration_payload.get("write_processed", False)),
                num_model_runs=int(configuration_payload.get("num_model_runs", 1)),
                restart_from_model=configuration_payload.get("restart_from_model"),
                mpi_tasks=configuration_payload.get("mpi_tasks"),
                mpi_no_spawn=bool(configuration_payload.get("mpi_no_spawn", False)),
                extra_arguments=[
                    str(item) for item in configuration_payload.get("extra_arguments", [])
                ],
            ),
        )


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _deserialize_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(str(value))
