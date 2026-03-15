# Roadmap

## Stage 0: Discovery and architecture

Deliverables:

- analyze `gprMax` and the historical `gprMax-Designer`;
- define architecture, project structure, and initial technical decisions;
- document product and engineering direction.

Exit criteria:

- architecture and integration strategy are documented;
- initial decisions are explicit and reviewable.

## Stage 1: Skeleton and app shell

Deliverables:

- repository layout and packaging metadata;
- runnable PySide6 application shell;
- main window with stable top-level navigation;
- placeholder views for welcome, model editor, runs, results, and settings;
- application context, logging bootstrap, and service skeletons.

Exit criteria:

- desktop app opens and navigates between screens;
- codebase has a clean baseline for iterative work.

## Stage 2: Project model, persistence, and settings

Deliverables:

- versioned project manifest format;
- create/open/save flows connected to the UI;
- recent projects with persisted metadata;
- project directory scaffolding;
- typed essential project model aligned with `gprMax` docs;
- project validation for persistence-stage rules;
- application settings persistence.

Exit criteria:

- users can create and reopen projects without touching raw files.

## Stage 3: `gprMax` integration layer and runner

Deliverables:

- subprocess adapter for `gprMax`;
- run request model;
- stdout/stderr capture;
- run history;
- validation before launch;
- failure reporting.

Exit criteria:

- a project can launch a real `gprMax` run from the GUI and preserve artifacts.

## Stage 4: Model editor MVP

Deliverables:

- guided forms for core model parameters;
- materials, geometry, sources, receivers, and grid primitives;
- validation and sensible defaults;
- generated input preview.

Exit criteria:

- non-programmer users can build a basic model without hand-writing input.

## Stage 5: Results viewer MVP

Deliverables:

- results browser by project and run;
- open result folder from UI;
- initial plots/metadata views for the most common outputs.

Exit criteria:

- users can inspect run outputs and identify where artifacts were written.

## Stage 6: Advanced mode

Deliverables:

- raw input editor and diff/preview with generated input;
- advanced run options;
- expert settings without degrading the guided flow.

Exit criteria:

- power users retain broad control over `gprMax` features.

## Stage 7: Packaging and installer

Deliverables:

- standalone build pipeline;
- Windows installer;
- first strategy for bundling or managing the `gprMax` runtime.

Exit criteria:

- a new user can install and open the application without manual Python setup.

## Stage 8: Documentation, tests, and release preparation

Deliverables:

- developer docs and contributor guidance;
- expanded unit and integration tests;
- release checklist and CI baseline.

Exit criteria:

- the project is ready for external contributors and early adopters.
