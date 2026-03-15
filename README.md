# GPRMax Workbench

`GPRMax Workbench` is a modern desktop GUI for `gprMax` built with Python and PySide6.

The project targets geophysicists, engineers, researchers, teachers, and students who need the power of `gprMax` without forcing them to work through raw CLI flows, handwritten input files, or Python environment setup.

## Goals

- make project creation and simulation runs accessible to non-programmers;
- keep `gprMax` as the source of truth for simulation capabilities;
- provide a clear path from GUI configuration to generated `gprMax` input;
- support both guided workflows and an advanced mode with raw input visibility;
- stay modular, testable, and maintainable as an open-source desktop application.

## Current status

This repository currently contains:

- Stage 0 discovery and architecture documentation;
- Stage 1 application skeleton with a runnable PySide6 shell;
- layered package structure for UI, application services, domain, infrastructure, and jobs;
- initial placeholders for project persistence, settings, logging, and `gprMax` integration.

## Repository structure

```text
docs/                     Architecture, roadmap, tech decisions
src/gprmax_workbench/     Application package
tests/                    Unit tests for core, non-UI parts
```

Inside `src/gprmax_workbench/`:

```text
ui/                       Qt windows, views, theme
application/              Use cases, app state, orchestration services
domain/                   Domain models and validation rules
infrastructure/           Settings, logging, persistence, gprMax adapters
jobs/                     Background job primitives
```

## Architecture direction

The GUI is intentionally decoupled from `gprMax` internals. The default integration strategy is `subprocess-first` through a dedicated adapter layer, which keeps the desktop app resilient to future `gprMax` changes and avoids binding the UI directly to internal modules.

Project state is persisted as a human-readable project manifest plus dedicated folders for generated input, run artifacts, and results.

## Development

Create a virtual environment and install dependencies:

```bash
pip install -e .[dev]
```

Run the application:

```bash
python -m gprmax_workbench
```

Run tests:

```bash
python -m unittest discover -s tests
```

## First implementation focus

The next engineering steps are:

1. flesh out project lifecycle and recent-project handling;
2. generate stable project manifests and generated `gprMax` input files;
3. implement the `gprMax` subprocess runner with logs, status tracking, and cancellation;
4. add the first guided model editor flow;
5. add a minimal results browser/viewer.

## References

- `gprMax`: https://github.com/gprMax/gprMax
- historical GUI reference only: https://github.com/tomsiwek/gprMax-Designer
