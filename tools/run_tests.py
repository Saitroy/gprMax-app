from __future__ import annotations

import os
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path


class _WorkspaceTemporaryDirectory:
    def __init__(
        self,
        suffix: str | None = None,
        prefix: str | None = None,
        dir: str | os.PathLike[str] | None = None,
        ignore_cleanup_errors: bool = False,
        delete: bool = True,
    ) -> None:
        self._suffix = suffix or ""
        self._prefix = prefix or "tmp"
        self._dir = Path(dir) if dir is not None else Path(tempfile.gettempdir())
        self._ignore_cleanup_errors = ignore_cleanup_errors
        self._delete = delete
        self.name = ""

    def __enter__(self) -> str:
        self.name = str(self._create())
        return self.name

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        if not self.name or not self._delete:
            return
        shutil.rmtree(self.name, ignore_errors=True)
        self.name = ""

    def _create(self) -> Path:
        self._dir.mkdir(parents=True, exist_ok=True)
        for _ in range(100):
            candidate = self._dir / f"{self._prefix}{uuid.uuid4().hex}{self._suffix}"
            try:
                candidate.mkdir()
            except FileExistsError:
                continue
            return candidate
        raise FileExistsError(f"Could not create a unique temporary directory in {self._dir}")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    temp_root = repo_root / ".tmp_test_runs"
    temp_root.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    tempfile.tempdir = str(temp_root)
    tempfile.TemporaryDirectory = _WorkspaceTemporaryDirectory

    os.chdir(repo_root)
    suite = unittest.defaultTestLoader.discover(start_dir="tests")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
