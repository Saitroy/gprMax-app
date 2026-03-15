from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from threading import Event, Thread
from typing import Callable
from io import TextIOBase


StdoutCallback = Callable[[str], None]
StderrCallback = Callable[[str], None]
CompletedCallback = Callable[[int, bool], None]


@dataclass(slots=True)
class RunningProcess:
    process: subprocess.Popen[str]
    command: list[str]
    working_directory: str
    cancel_requested: Event = field(default_factory=Event)

    def cancel(self) -> None:
        self.cancel_requested.set()
        if self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            self.process.kill()


class SubprocessMonitor:
    """Executes a subprocess and streams stdout/stderr through callbacks."""

    def start(
        self,
        command: list[str],
        *,
        working_directory: str,
        on_stdout: StdoutCallback,
        on_stderr: StderrCallback,
        on_completed: CompletedCallback,
    ) -> RunningProcess:
        process = subprocess.Popen(
            command,
            cwd=working_directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        running = RunningProcess(
            process=process,
            command=list(command),
            working_directory=working_directory,
        )

        stdout_thread = Thread(
            target=self._consume_stream,
            args=(process.stdout, on_stdout),
            daemon=True,
        )
        stderr_thread = Thread(
            target=self._consume_stream,
            args=(process.stderr, on_stderr),
            daemon=True,
        )
        waiter_thread = Thread(
            target=self._wait_for_completion,
            args=(running, stdout_thread, stderr_thread, on_completed),
            daemon=True,
        )

        stdout_thread.start()
        stderr_thread.start()
        waiter_thread.start()
        return running

    def _consume_stream(
        self,
        stream: TextIOBase | None,
        callback: Callable[[str], None],
    ) -> None:
        if stream is None:
            return
        try:
            for line in iter(stream.readline, ""):
                callback(line)
        finally:
            stream.close()

    def _wait_for_completion(
        self,
        running: RunningProcess,
        stdout_thread: Thread,
        stderr_thread: Thread,
        on_completed: CompletedCallback,
    ) -> None:
        exit_code = running.process.wait()
        stdout_thread.join()
        stderr_thread.join()
        on_completed(exit_code, running.cancel_requested.is_set())
