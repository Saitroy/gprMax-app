# Current State

Last updated: 2026-04-07

This document describes the current implemented product state. It is intentionally factual and should be read as a companion to the architectural and roadmap documents.

## Entry Points

The application can be started through any of the following entry points:

- `python -m gprmax_workbench`
- `python -m gprmax_workbench --project <path-to-project>`
- `gprmax-workbench` after `pip install -e .`

## User-Facing Workspaces

### Welcome

The start screen is a dedicated workspace, not a placeholder.

Current responsibilities:

- create a new project;
- open an existing project;
- reopen recent projects;
- show current workspace readiness and latest run activity;
- surface documentation and bundled example projects.

### Project

The project workspace is a sectioned editor instead of one long form.

Current sections:

- `Scene`
- `Domain / Grid / Time Window`
- `Materials`
- `Waveforms`
- `Sources`
- `Receivers`
- `Geometry`
- `Libraries / Imports`
- `Advanced`
- `Input Preview`

The scene section currently provides:

- orthographic `XY / XZ / YZ` views;
- selection inspector with exact coordinate editing;
- snap-to-grid and step-based nudging;
- duplicate/delete actions;
- visible splitter handles and adaptive side-panel behavior.

### Simulation

The simulation workspace is separate from editing and remains focused on run orchestration.

Current capabilities:

- run readiness summary;
- run configuration editing;
- input preview and export;
- start, retry, and cancel actions;
- live combined log view;
- run history;
- open run/output folders.

### Results

The results workspace is run-centric.

Current capabilities:

- browse finished runs;
- inspect discovered output files and other artifacts;
- view summary metadata;
- inspect A-scan traces;
- inspect bounded B-scan previews when source data allows it;
- open selected files and output directories.

### Settings

Settings are currently exposed as a dialog, not a top-level navigation page.

Current capabilities:

- language selection;
- advanced mode toggle;
- external runtime fallback path;
- runtime, capability, and diagnostics summary.

## Desktop Layout Baseline

The current UI baseline is desktop-first.

Verified targets:

- `1366x768`
- `1920x1080`

Current layout behavior:

- separate `Welcome`, `Project`, `Simulation`, and `Results` workspaces;
- adaptive splitters with visible drag handles across the main tools;
- scene, simulation, and results layouts avoid forcing one overloaded mega-screen;
- side panels can be resized by the user with the mouse.

## Current Technical Boundaries

The current implementation is intentionally bounded in a few places:

- the first public installer pipeline is not finished;
- splitter sizes are not yet persisted between sessions;
- guided editor coverage does not yet span the full `gprMax` command surface;
- results analysis is currently limited to the existing A-scan and bounded B-scan workflows;
- public release support processes such as CI, issue templates, and crash bundle workflows are still incomplete.

## Verification Snapshot

Latest local verification used for this documentation update:

- `python -m unittest discover tests` -> `107 OK`
- offscreen UI smoke confirms stable shell behavior at `1366x768` and `1920x1080`

## Related Documents

- [README](../README.md)
- [Architecture](./ARCHITECTURE.md)
- [UI Workstream](./UI_WORKSTREAM.md)
- [First Release Readiness](./FIRST_RELEASE_READINESS.md)
