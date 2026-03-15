from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gprmax-workbench",
        description="Launch the GPRMax Workbench desktop application.",
    )
    parser.add_argument(
        "--project",
        help="Optional path to a project directory to open on startup.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        from .app import run
    except ModuleNotFoundError as exc:
        if exc.name == "PySide6":
            sys.stderr.write(
                "PySide6 is not installed. Install project dependencies before launching the GUI.\n"
            )
            return 2
        raise

    return run(initial_project=args.project)


if __name__ == "__main__":
    raise SystemExit(main())
