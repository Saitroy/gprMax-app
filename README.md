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
- Stage 2 foundation layer with project model, validation, persistence, and settings flows;
- layered package structure for UI, application services, domain, infrastructure, and jobs.

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

The Stage 2 project model mirrors the `gprMax` documentation at a foundation level:

- essential domain settings (`domain`, `dx_dy_dz`, `time_window`, PML);
- materials;
- waveforms;
- sources and receivers;
- ordered geometry primitives as future editor-backed commands;
- optional advanced raw input overrides.

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

1. implement the Stage 3 `gprMax` subprocess runner with logs, status tracking, and cancellation;
2. generate actual `.in` files from the Stage 2 project model;
3. add the first guided model editor flow for materials, waveforms, and antennas;
4. add a minimal results browser/viewer;
5. prepare packaging/runtime-discovery decisions for Windows distribution.

## References

- `gprMax`: https://github.com/gprMax/gprMax
- historical GUI reference only: https://github.com/tomsiwek/gprMax-Designer
