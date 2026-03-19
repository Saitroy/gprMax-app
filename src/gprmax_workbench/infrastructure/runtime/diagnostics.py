from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ...domain.capability_status import CapabilityLevel, CapabilityStatus
from ...domain.engine_config import EngineResolution, EngineMode
from ...domain.runtime_info import RuntimeInfo
from .path_manager import PathManager
from .versioning import VersioningService


@dataclass(slots=True)
class ProbeResult:
    python_exists: bool
    module_available: bool
    gprmax_version: str | None
    gpu_available: bool
    mpi_available: bool
    error: str | None = None


class RuntimeProbe(Protocol):
    def probe(self, python_executable: Path, module_name: str) -> ProbeResult:
        ...


class SubprocessRuntimeProbe:
    """Checks runtime capabilities without importing gprMax into the GUI process."""

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self._timeout_seconds = timeout_seconds

    def probe(self, python_executable: Path, module_name: str) -> ProbeResult:
        if not python_executable.exists():
            return ProbeResult(
                python_exists=False,
                module_available=False,
                gprmax_version=None,
                gpu_available=False,
                mpi_available=False,
                error=f"Python executable not found: {python_executable}",
            )

        script = """
import importlib
import importlib.util
import json

def has(name):
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False

payload = {
    "gprmax": has("gprMax"),
    "gpu": has("pycuda"),
    "mpi": has("mpi4py"),
    "version": None,
}
if payload["gprmax"]:
    try:
        module = importlib.import_module("gprMax")
        payload["version"] = getattr(module, "__version__", None)
    except Exception:
        payload["version"] = None
print(json.dumps(payload))
"""
        try:
            completed = subprocess.run(
                [str(python_executable), "-c", script],
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            return ProbeResult(
                python_exists=False,
                module_available=False,
                gprmax_version=None,
                gpu_available=False,
                mpi_available=False,
                error=f"Python executable not found: {python_executable}",
            )
        except subprocess.TimeoutExpired:
            return ProbeResult(
                python_exists=True,
                module_available=False,
                gprmax_version=None,
                gpu_available=False,
                mpi_available=False,
                error="Timed out while checking the gprMax runtime.",
            )

        if completed.returncode != 0:
            error = completed.stderr.strip() or completed.stdout.strip()
            return ProbeResult(
                python_exists=True,
                module_available=False,
                gprmax_version=None,
                gpu_available=False,
                mpi_available=False,
                error=error or "gprMax runtime probe failed.",
            )

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return ProbeResult(
                python_exists=True,
                module_available=False,
                gprmax_version=None,
                gpu_available=False,
                mpi_available=False,
                error="Could not parse runtime probe output.",
            )

        return ProbeResult(
            python_exists=True,
            module_available=bool(payload.get("gprmax")),
            gprmax_version=payload.get("version"),
            gpu_available=bool(payload.get("gpu")),
            mpi_available=bool(payload.get("mpi")),
            error=None
            if bool(payload.get("gprmax"))
            else (
                f"gprMax module '{module_name}' is not available in {python_executable}."
            ),
        )


class RuntimeDiagnostics:
    """Builds a runtime health report for bundled-first execution."""

    def __init__(
        self,
        *,
        path_manager: PathManager,
        versioning: VersioningService,
        probe: RuntimeProbe | None = None,
    ) -> None:
        self._path_manager = path_manager
        self._versioning = versioning
        self._probe = probe or SubprocessRuntimeProbe()

    def inspect(self, resolution: EngineResolution) -> RuntimeInfo:
        engine = resolution.engine
        manifest = self._versioning.load_engine_manifest(
            self._path_manager.bundled_manifest_path
        )
        diagnostics = list(resolution.notes)

        if engine.mode == EngineMode.BUNDLED and engine.engine_root is not None:
            if not engine.engine_root.exists():
                diagnostics.append(
                    f"Bundled engine directory is missing: {engine.engine_root}"
                )
            if not self._path_manager.bundled_manifest_path.exists():
                diagnostics.append(
                    f"Bundled engine manifest is missing: {self._path_manager.bundled_manifest_path}"
                )

        probe_result = self._probe.probe(engine.python_executable, engine.module_name)
        if probe_result.error:
            diagnostics.append(probe_result.error)

        capabilities = self._build_capabilities(probe_result)

        return RuntimeInfo(
            engine=engine,
            app_version=self._versioning.app_version(),
            bundled_engine_version=manifest.get("engine_version"),
            gprmax_version=probe_result.gprmax_version or manifest.get("gprmax_version"),
            settings_path=self._path_manager.settings_directory / "settings.json",
            logs_directory=self._path_manager.logs_directory,
            cache_directory=self._path_manager.cache_directory,
            temp_directory=self._path_manager.temp_directory,
            capabilities=capabilities,
            diagnostics=diagnostics,
            is_healthy=probe_result.python_exists and probe_result.module_available,
        )

    def _build_capabilities(self, probe_result: ProbeResult) -> list[CapabilityStatus]:
        cpu_level = (
            CapabilityLevel.READY
            if probe_result.python_exists and probe_result.module_available
            else CapabilityLevel.UNAVAILABLE
        )
        cpu_detail = (
            ""
            if cpu_level == CapabilityLevel.READY
            else "The base gprMax runtime is not healthy."
        )
        if cpu_level == CapabilityLevel.READY:
            gpu_level = (
                CapabilityLevel.READY
                if probe_result.gpu_available
                else CapabilityLevel.OPTIONAL
            )
            mpi_level = (
                CapabilityLevel.READY
                if probe_result.mpi_available
                else CapabilityLevel.OPTIONAL
            )
            gpu_detail = (
                ""
                if probe_result.gpu_available
                else "pycuda is not available in the current runtime."
            )
            mpi_detail = (
                ""
                if probe_result.mpi_available
                else "mpi4py is not available in the current runtime."
            )
        else:
            gpu_level = CapabilityLevel.UNAVAILABLE
            mpi_level = CapabilityLevel.UNAVAILABLE
            gpu_detail = (
                "GPU execution is unavailable because the base gprMax runtime is not healthy."
            )
            mpi_detail = (
                "MPI execution is unavailable because the base gprMax runtime is not healthy."
            )

        return [
            CapabilityStatus(code="cpu", level=cpu_level, detail=cpu_detail),
            CapabilityStatus(code="gpu", level=gpu_level, detail=gpu_detail),
            CapabilityStatus(code="mpi", level=mpi_level, detail=mpi_detail),
        ]
