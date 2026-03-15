# Architecture

## Product framing

`GPRMax Workbench` is a desktop application that wraps `gprMax` with a guided UI, project system, run management, and results access. It is not a fork of `gprMax` and not a rewrite of `gprMax-Designer`.

The desktop app owns:

- project lifecycle;
- user-facing forms and workflows;
- validation and defaults;
- generation of `gprMax` input artifacts;
- simulation orchestration and logging;
- results discovery and viewing.

`gprMax` remains the computation engine and functional source of truth.

## Architectural principles

- layered structure with explicit boundaries;
- UI depends on application services, not on `gprMax` internals;
- integration with `gprMax` is isolated behind adapters;
- project metadata is persisted independently from generated simulation artifacts;
- long-running work is represented as jobs, not run on the UI thread;
- the generated `gprMax` input file is a transparent artifact, not a hidden internal detail.

## Layers

### `ui/`

Responsibilities:

- windows, dialogs, views, view composition;
- navigation, actions, empty/error/loading states;
- presentation models for widgets and forms.

Rules:

- should not spawn `gprMax` directly;
- should not know process arguments or filesystem layouts beyond data exposed by services.

### `application/`

Responsibilities:

- use-case orchestration;
- application/session state;
- project lifecycle coordination;
- simulation preparation and results coordination.

Rules:

- may coordinate multiple infrastructure services;
- should express product workflows in stable interfaces that UI can consume.

### `domain/`

Responsibilities:

- core entities such as project, run record, and result set;
- validation rules and business constraints;
- stable concepts that are not tied to Qt or process execution.

### `infrastructure/`

Responsibilities:

- project persistence;
- settings storage;
- logging setup;
- filesystem interactions;
- `gprMax` adapter implementations.

### `jobs/`

Responsibilities:

- background job contracts and job state;
- cancellation primitives;
- future execution queue integration.

## Data flow

1. User edits project/model data in the GUI.
2. UI sends commands to application services.
3. Application services validate input and persist project state.
4. An input-generation service serializes project state into a `gprMax` input artifact.
5. A simulation service creates a typed run configuration and passes it to the `gprMax` adapter.
6. A subprocess runner launches `gprMax`, streams stdout/stderr, and writes run artifacts.
7. A run repository persists metadata/history and exposes it back to the UI.
8. Results services can later index run outputs and expose them back to the UI.

## Stage 4 model editor foundation

The current model editor deliberately uses a form-first architecture instead of a canvas/CAD scene builder.

Why:

- it matches the current project model and input-generation maturity;
- it keeps the GUI understandable for non-programmers;
- it gives a stable path to validation, persistence, and preview;
- it avoids baking a weak visual scene model into the long-term architecture too early.

Top-level editor composition:

- summary/header card with project location and validation state;
- tabbed sections for general settings, materials, waveforms, sources, receivers, geometry, and input preview;
- list-detail editors inside entity tabs;
- application-layer mutation services that update `AppState` and validation state directly.

The editor does not generate input lines or subprocess commands itself. It only edits the typed project model and asks dedicated services for validation and preview.

## `gprMax` integration strategy

### Recommended default: subprocess-first

The preferred integration mode is launching `gprMax` as an external process, typically via:

```text
python -m gprMax <input-file> [options]
```

Why this is the default:

- it matches `gprMax`'s public CLI contract;
- it is less coupled to internal module structure;
- it naturally exposes stdout/stderr for logs;
- it keeps GPU/MPI/runtime concerns outside the GUI process;
- it is easier to support across future `gprMax` versions.

### Secondary mode: optional hybrid integration

Some future features may benefit from controlled direct imports of a public `gprMax` Python API, but only behind the same adapter boundary and only where the import path is stable enough.

The UI should never care whether a run came from subprocess mode or a future in-process implementation.

## Stage 3 execution foundation

The current runner is intentionally scoped to a minimum viable but extensible subset.

Directly supported now:

- essential domain commands;
- materials;
- waveforms;
- receivers;
- source subset: `hertzian_dipole`, `magnetic_dipole`, `voltage_source`;
- geometry subset: `box`, `sphere`, `cylinder`;
- `geometry_view`;
- geometry-only execution mode;
- GPU flag wiring;
- future hooks for `-mpi`, `--mpi-no-spawn`, `-n`, `-restart`, `--write-processed`.

Deferred deliberately:

- broad object-command coverage;
- full HPC orchestration;
- structured results parsing;
- advanced recovery/retry policies;
- a polished expert run configuration UX.

## Run artifact layout

Stage 3 run folders use the following structure:

```text
project/
  runs/
    20260315-153000-ab12cd34/
      input/
        simulation.in
      logs/
        stdout.log
        stderr.log
        combined.log
      output/
      metadata.json
```

Rationale:

- one immutable folder per run;
- explicit separation of input snapshot, logs, and outputs;
- metadata remains human-readable and testable;
- future results viewers can target `runs/<run-id>/output` without guessing.

## Project layout on disk

Proposed project folder layout:

```text
MyProject/
  project.gprwb.json
  generated/
    current.in
  runs/
    20260315-153000/
      command.json
      stdout.log
      stderr.log
      generated.in
      output/
  results/
  assets/
```

Notes:

- `project.gprwb.json` stores editor-facing project state;
- `generated/` stores reproducible generated input files;
- `runs/` stores immutable execution artifacts and logs;
- `results/` can contain indexed or curated outputs exposed by viewers.

## Stage 2 project model

The persisted project manifest is intentionally aligned to `gprMax` command families from the official documentation instead of arbitrary GUI-only groupings.

Current typed sections:

- `metadata`: project identity and timestamps;
- `model.domain`: domain size, spatial resolution, time window, PML cells;
- `model.notes` and `model.tags`: editor-facing metadata for guided workflows;
- `model.materials`: material definitions;
- `model.waveforms`: waveform definitions;
- `model.sources`: source definitions with waveform references;
- `model.receivers`: receiver definitions;
- `model.geometry`: ordered geometry primitives with parameters, material references, labels, notes, tags, and dielectric-smoothing flag;
- `model.geometry_views`: geometry-view requests;
- `advanced.raw_input_overrides`: raw text hooks for later advanced mode.

This gives us a stable persistence contract now without pretending that Stage 2 already supports the full `gprMax` editor surface.

## Project file format

Project manifest file: `project.gprwb.json`

Format shape:

```json
{
  "schema": {
    "name": "gprmax-workbench-project",
    "version": 1
  },
  "metadata": {},
  "model": {
    "title": "",
    "notes": "",
    "tags": [],
    "domain": {},
    "materials": [],
    "waveforms": [],
    "sources": [],
    "receivers": [],
    "geometry": [],
    "geometry_views": [],
    "python_blocks": []
  },
  "advanced": {
    "raw_input_overrides": []
  }
}
```

Rationale:

- human-readable and diff-friendly for open-source work;
- versioned schema from the start;
- clear separation between editable project state and generated/run artifacts;
- enough structure to drive Stage 3 generation and validation without locking us into a fake full editor too early.

## Stage 4 editor services

The Stage 4 editor introduces three application-level services:

- `ModelEditorService`: owns in-memory CRUD operations for model entities and marks the current project dirty;
- `ValidationService`: exposes filtered validation results for editor sections and summary banners;
- `InputPreviewService`: builds/export previews from the current project without touching the run lifecycle.

This keeps the UI thin enough to stay replaceable while still giving the editor direct, low-latency feedback.

## UI shell

The Stage 1 shell is organized around five top-level workspaces:

- Welcome / Project Manager
- Model Editor
- Simulation Runner
- Results Viewer
- Settings

This gives a stable navigation model without prematurely locking the internal editor architecture.
