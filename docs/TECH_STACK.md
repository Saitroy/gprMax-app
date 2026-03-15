# Tech Stack

## Core stack

- Python
- PySide6
- Qt6 ecosystem

This stack is the default for the first release line.

## Why PySide6

- native desktop capability with a mature widget toolkit;
- strong Windows support, which is the initial priority platform;
- good long-term fit for multi-panel scientific tooling;
- Qt threading, models, and dockable UI patterns fit the product well;
- avoids the packaging and runtime complexity of a web-shell stack.

## Why not build on `gprMax-Designer`

`gprMax-Designer` is useful as a historical UX reference, but it should not be the architectural base for the new project. The new app needs:

- a layered architecture;
- typed Python modules with clearer boundaries;
- modern packaging and maintainability;
- a stable adapter boundary around `gprMax`.

## `gprMax` integration

### Default strategy

Use a `subprocess-first` adapter that launches `gprMax` through its CLI contract.

Typical invocation target:

```text
python -m gprMax <input-file> [options]
```

### Why this is preferred

- lower coupling to internal package structure;
- clearer capture of logs and exit codes;
- better isolation of heavy runtime concerns;
- easier compatibility story across `gprMax` releases.

### Hybrid path later

If specific features benefit from a stable Python API, add them behind the same adapter interface. The UI and application layers should continue to speak to an abstract `GprMaxAdapter`.

## Background work

Stage 1 keeps job primitives simple. As run orchestration matures, background execution should use Qt-friendly workers for UI integration while keeping job specifications independent from the view layer.

## Persistence

- project manifest: JSON in the project root;
- application settings: JSON under user application data;
- run artifacts: dedicated per-run folders with logs and generated input snapshots.

## Packaging strategy

Initial recommendation:

- application bundling: `PyInstaller`;
- Windows installer: `Inno Setup` or `WiX`, with `Inno Setup` preferred first for faster iteration;
- release focus: Windows first, cross-platform later.

This is the pragmatic path for an MVP. If startup time or binary size become serious issues, reevaluate `Nuitka` later with real profiling data.
