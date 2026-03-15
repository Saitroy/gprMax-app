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
- Stage 3 subprocess-first integration with `gprMax`, input generation, run artifacts, live logs, and run history;
- Stage 4 model editor MVP with guided forms for essential model setup, materials, waveforms, sources, receivers, geometry, and input preview;
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

Stage 3 currently supports:

- input generation for the essential domain commands;
- materials, waveforms, receivers, a limited source subset, and a limited geometry subset;
- subprocess execution through `python -m gprMax`;
- geometry-only mode;
- GPU flag wiring;
- future-ready hooks for MPI and batch-related CLI flags;
- persisted run metadata, logs, and output directories per run.

Stage 4 currently supports:

- form-based editing of project/model overview data;
- CRUD flows for materials, waveforms, sources, receivers, and a focused geometry subset;
- model validation wired to editor state and save flow;
- generated input preview from the current in-memory model;
- direct wiring from model editor state into persistence and the existing simulation runner.

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

1. expand input generation and editor coverage across more `gprMax` commands and model entities;
2. add a minimal results browser/viewer on top of run artifacts;
3. harden cancellation/error handling with real-world `gprMax` runtime testing;
4. prepare packaging/runtime-discovery decisions for Windows distribution;
5. design the first advanced-mode bridge for raw input overrides and power-user workflows.

## References

- `gprMax`: https://github.com/gprMax/gprMax
- historical GUI reference only: https://github.com/tomsiwek/gprMax-Designer
