# Architectural Decisions

## 2026-03-15: Use `GPRMax Workbench` / `gprmax_workbench` as the initial project name

Status: accepted

Rationale:

- clearly tied to the `gprMax` ecosystem;
- sounds like a serious engineering tool, not a demo app;
- neutral enough for open-source contributors and institutional users.

## 2026-03-15: Build the GUI with PySide6 and Qt6

Status: accepted

Rationale:

- matches the desktop-first product goal;
- gives strong Windows support and a mature widget ecosystem;
- supports long-lived scientific tooling better than lightweight GUI stacks.

## 2026-03-15: Treat `gprMax` as the source of truth and isolate it behind an adapter

Status: accepted

Rationale:

- the desktop app should not duplicate or reinterpret core simulation behavior;
- integration needs a stable seam so `gprMax` upgrades do not force UI rewrites;
- this keeps the GUI testable without loading the full runtime.

## 2026-03-15: Prefer `subprocess-first` integration with `gprMax`

Status: accepted

Rationale:

- the CLI is the most stable and observable execution surface;
- process isolation improves failure handling and log capture;
- direct imports remain a possible optimization, not the architectural baseline.

Consequence:

- run requests, logs, exit codes, and artifacts become first-class domain/application concepts;
- later hybrid integrations must conform to the same adapter contract.

## 2026-03-15: Keep project state separate from generated and executed artifacts

Status: accepted

Rationale:

- users need both clean editable project data and reproducible run history;
- generated `.in` files and run logs should be inspectable and preserved;
- this supports transparency for both novice and advanced users.

## 2026-03-15: Use a versioned JSON project manifest aligned with `gprMax` command families

Status: accepted

Rationale:

- Stage 2 needs stable persistence before a full editor exists;
- the data model should reflect `gprMax` concepts such as domain, materials, waveforms, sources, receivers, and geometry;
- JSON keeps the file easy to diff, inspect, and test;
- ordered geometry entries preserve future command-generation order without forcing premature GUI abstractions.

## 2026-03-15: Keep Stage 3 execution subprocess-first and artifact-centric

Status: accepted

Rationale:

- `gprMax` has a documented CLI surface that is more stable than direct UI-level imports;
- stdout/stderr capture and per-run folders are easier to reason about than in-process execution side effects;
- this keeps run history, cancellation, error reporting, and future post-processing grounded in explicit artifacts.

Consequence:

- each run gets its own metadata manifest and log files;
- the UI talks to application services and run records, not to `subprocess.Popen`;
- a future hybrid API path must still conform to the same run-artifact contract.
