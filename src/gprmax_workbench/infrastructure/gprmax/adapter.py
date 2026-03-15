from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Sequence


@dataclass(slots=True)
class GprMaxRunRequest:
    working_directory: Path
    input_file: Path
    arguments: Sequence[str] = field(default_factory=tuple)


@dataclass(slots=True)
class GprMaxProcessHandle:
    process: subprocess.Popen[str]
    command: list[str]


class GprMaxAdapter(Protocol):
    def build_command(self, request: GprMaxRunRequest) -> list[str]:
        ...

    def describe_runtime(self) -> str:
        ...


class SubprocessGprMaxAdapter:
    """Launches gprMax through the Python module CLI boundary."""

    def __init__(
        self,
        python_executable: str | None = None,
        module_name: str = "gprMax",
    ) -> None:
        self._python_executable = python_executable or sys.executable
        self._module_name = module_name

    def build_command(self, request: GprMaxRunRequest) -> list[str]:
        return [
            self._python_executable,
            "-m",
            self._module_name,
            str(request.input_file),
            *request.arguments,
        ]

    def describe_runtime(self) -> str:
        return f"{self._python_executable} -m {self._module_name}"

    def launch(self, request: GprMaxRunRequest) -> GprMaxProcessHandle:
        command = self.build_command(request)
        process = subprocess.Popen(
            command,
            cwd=request.working_directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return GprMaxProcessHandle(process=process, command=command)
