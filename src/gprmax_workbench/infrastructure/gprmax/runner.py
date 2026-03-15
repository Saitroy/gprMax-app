from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .process_monitor import RunningProcess, SubprocessMonitor


@dataclass(slots=True)
class RunnerCallbacks:
    on_stdout: Callable[[str], None]
    on_stderr: Callable[[str], None]
    on_completed: Callable[[int, bool], None]


class GprMaxSubprocessRunner:
    """Thin orchestration wrapper around the generic subprocess monitor."""

    def __init__(self, monitor: SubprocessMonitor | None = None) -> None:
        self._monitor = monitor or SubprocessMonitor()

    def start(
        self,
        command: list[str],
        *,
        working_directory: Path,
        callbacks: RunnerCallbacks,
    ) -> RunningProcess:
        return self._monitor.start(
            command=command,
            working_directory=str(working_directory),
            on_stdout=callbacks.on_stdout,
            on_stderr=callbacks.on_stderr,
            on_completed=callbacks.on_completed,
        )
