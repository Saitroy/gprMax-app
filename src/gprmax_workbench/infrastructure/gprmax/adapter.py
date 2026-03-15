from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ...domain.gprmax_config import GprMaxRuntimeConfig, SimulationRunConfig
from .command_builder import GprMaxCommandBuilder, GprMaxCommandRequest


@dataclass(slots=True)
class GprMaxExecutionRequest:
    working_directory: Path
    input_file: Path
    configuration: SimulationRunConfig


class GprMaxAdapter(Protocol):
    def build_command(self, request: GprMaxExecutionRequest) -> list[str]:
        ...

    def describe_runtime(self) -> str:
        ...

    def runtime_config(self) -> GprMaxRuntimeConfig:
        ...

    def probe_runtime(self, timeout_seconds: float = 5.0) -> tuple[bool, str]:
        ...


class SubprocessGprMaxAdapter:
    """Builds commands and runtime checks for subprocess-based gprMax execution."""

    def __init__(
        self,
        python_executable: str | None = None,
        module_name: str = "gprMax",
        command_builder: GprMaxCommandBuilder | None = None,
    ) -> None:
        self._runtime = GprMaxRuntimeConfig(
            python_executable=python_executable or sys.executable,
            module_name=module_name,
        )
        self._command_builder = command_builder or GprMaxCommandBuilder()

    def build_command(self, request: GprMaxExecutionRequest) -> list[str]:
        return self._command_builder.build(
            runtime=self._runtime,
            request=GprMaxCommandRequest(
                working_directory=request.working_directory,
                input_file=request.input_file,
                configuration=request.configuration,
            ),
        )

    def describe_runtime(self) -> str:
        return f"{self._runtime.python_executable} -m {self._runtime.module_name}"

    def runtime_config(self) -> GprMaxRuntimeConfig:
        return self._runtime

    def configure_runtime(
        self,
        python_executable: str | None,
        module_name: str | None = None,
    ) -> None:
        self._runtime = GprMaxRuntimeConfig(
            python_executable=python_executable or sys.executable,
            module_name=module_name or self._runtime.module_name,
        )

    def probe_runtime(self, timeout_seconds: float = 5.0) -> tuple[bool, str]:
        command = [
            self._runtime.python_executable,
            "-c",
            (
                "import importlib.util,sys;"
                f"sys.exit(0 if importlib.util.find_spec('{self._runtime.module_name}') else 1)"
            ),
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except FileNotFoundError:
            return False, f"Python executable not found: {self._runtime.python_executable}"
        except subprocess.TimeoutExpired:
            return False, "Timed out while checking the gprMax runtime."

        if completed.returncode == 0:
            return True, self.describe_runtime()
        return (
            False,
            f"gprMax module '{self._runtime.module_name}' is not available in {self._runtime.python_executable}.",
        )
