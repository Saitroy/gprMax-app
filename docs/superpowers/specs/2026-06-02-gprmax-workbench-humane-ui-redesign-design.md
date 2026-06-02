# gprMax Workbench Humane UI Redesign

Date: 2026-06-02

## Goal

Redesign the existing PySide6 desktop application into a calm engineering
workbench for geophysicists and engineers who may have no programming
experience. Preserve the current capabilities while making the common path
obvious, compact, and responsive.

The visual direction is based on the provided reference and the approved
visual companion mockups:

- light gray application background;
- white working surfaces with thin borders;
- restrained blue primary actions;
- semantic green, amber, and red status colors;
- compact spacing with a clear visual hierarchy;
- technical detail available on demand instead of permanently occupying space.

## Confirmed User Decisions

- The primary audience is geophysicists and engineers without programming
  experience.
- The main workspace after opening a project is the visual scene.
- The scene must show the model and support editing of layers and anomalies.
- Mouse editing and exact numeric editing are equally important and remain
  synchronized.
- The interface should be tidy and compact.
- Long internal navigation should not permanently occupy the workspace.
- Home should be a light start screen with create, open, recent projects, and
  one example.
- Approved editor direction: option A, "Engineering scene".
- Approved supporting screens: Home, Simulation setup, and Results A-scan.

## Existing UI Audit

The current palette in `src/gprmax_workbench/ui/theme.py` is already close to
the requested reference. The main problems are information density and
unnecessary refresh work.

### Usability Issues

- The editor gives too much permanent space to secondary sections and too
  little space to the scene.
- Forms, summaries, toolbars, and internal navigation compete for attention.
- The common route from model creation to simulation is less clear than the
  available feature set.
- Technical parameters appear too early for users who only need the basic
  workflow.

### Performance Issues

- `ProjectView._on_model_changed()` refreshes validation, refreshes choices,
  and calls `SceneCanvasPanel.set_project()` after editor changes.
- `SceneCanvasPanel.set_project()` calls `_refresh_scene()`.
- `_refresh_scene()` clears and rebuilds the graphics scene.
- Numeric and text inputs are connected to change handlers, so typing or
  adjusting values can trigger expensive full scene rebuilds.
- `MainWindow` also performs periodic shell and simulation state refreshes.
  These should avoid style repolish or view work when values did not change.

## Application Shell

Use one narrow global navigation rail with icons and tooltips:

1. Home
2. Model
3. Simulation
4. Results
5. Diagnostics
6. Settings

The active screen is visually clear. Secondary actions stay in the current
screen rather than expanding the global rail. The top bar remains compact and
contains:

- current screen and breadcrumb;
- unsaved state when relevant;
- compact readiness or run status;
- one primary action for the current screen.

Projects remain accessible from Home and the application menu. Avoid a
permanent full-width Projects screen unless the existing project lifecycle
requires it.

## Home

Home is a quiet entry point, not a dashboard full of cards.

Visible immediately:

- Create project;
- Open project;
- recent project list;
- one learning example;
- compact runtime readiness state.

Detailed environment paths and raw diagnostics stay behind Diagnostics or
Settings. If runtime is not configured, replace the small ready state with an
actionable warning and a direct setup action.

## Model Editor

The scene is the dominant workspace.

### Layout

Use a three-column desktop layout:

- left: compact scene layer list;
- center: large canvas;
- right: contextual exact inspector.

The left layer list shows model structure and selection:

- domain;
- material layers;
- anomalies;
- sources;
- receivers.

Less frequent areas such as waveform libraries, imported geometry internals,
raw commands, Python blocks, and advanced PML settings remain available
through contextual panels or collapsible advanced sections.

### Canvas

The canvas provides:

- selection;
- add;
- move;
- resize;
- zoom and fit;
- grid visibility;
- grid snapping;
- clear selected-object handles;
- visual source and receiver markers.

The canvas stays usable when the right inspector is collapsed. Splitters use
reasonable minimum sizes and remember layout where practical.

### Exact Inspector

Selecting an object on the canvas or in the layer list opens its contextual
inspector on the right. The inspector changes content for domain, layer,
anomaly, source, and receiver selection.

Common values remain open:

- X, Y, Z coordinates;
- width, length, height where relevant;
- material;
- grid step;
- snap setting.

Rare values go into a collapsed `Advanced` section. Units remain visible next
to numeric fields. Mouse edits update fields, and numeric edits update a
lightweight scene preview.

### Validation

Show a compact readiness summary in the top bar. Inline field errors appear
near the relevant input. Clicking a validation issue focuses the object and
field that need attention. Warnings do not block progress unless the
simulation cannot run correctly.

## Simulation

Simulation uses three internal states without creating a large permanent
navigation tree:

1. Setup
2. Run monitor
3. History

### Setup

The setup screen contains:

- run mode;
- run count;
- data persistence choices;
- preview input action;
- start action;
- compact readiness checklist on the right.

MPI, GPU selection, restart, and extra arguments remain available under an
advanced section. When Start is disabled, the UI explains the exact reason and
links back to the relevant editor object or runtime setup.

### Run Monitor

During execution show:

- running status;
- current stage;
- elapsed time;
- progress when available;
- concise live log summary;
- cancel action;
- output folder action.

After completion, provide a clear Results action. Technical logs remain
expandable.

## Results

Results gives the primary visualization most of the workspace.

### Layout

- left: compact run history;
- top: output, receiver, and component selectors;
- center: large chart area;
- right: small metadata panel;
- secondary areas: B-scan, summary, files, and export.

A-scan remains the default approved view. B-scan and file artifacts stay easy
to reach but do not displace the chart. Include empty, loading, unreadable
output, partial output, and completed states.

## Diagnostics And Settings

Diagnostics uses plain language first:

- what failed;
- what it affects;
- what the user should do next.

Technical paths, raw logs, and exportable diagnostics remain collapsible.

Settings stays compact and groups:

- language;
- runtime configuration;
- appearance when supported;
- advanced mode;
- performance defaults;
- reset layout.

Preserve RU and EN localization for all user-visible text.

## Performance Design

The redesign must address interaction freezes as part of the first
implementation pass.

### Scene Update Strategy

Separate lightweight preview updates from committed model updates:

- mouse drag updates only the affected graphics item and inspector values;
- numeric input updates only the selected graphics item preview;
- committed edits update only affected scene items when possible;
- full scene rebuild remains a fallback for project replacement, major
  structural changes, or explicit refresh.

### Validation Strategy

- Debounce expensive whole-model validation after rapid edits.
- Keep basic local field constraints immediate.
- Avoid refreshing every editor panel when one object changes.
- Refresh dependent choices only when the edited property affects them.

### Shell Refresh Strategy

- Skip shell label or style updates when the displayed state did not change.
- Avoid periodic view work while no simulation is active.
- Keep timer callbacks cheap and side-effect limited.

## States And Accessibility

Support at minimum:

- normal;
- empty;
- disabled with reason;
- warning;
- validation error;
- runtime unavailable;
- unsaved;
- running;
- completed;
- cancelled;
- failed;
- partial results.

Keyboard focus remains visible. Icons require tooltips. Colors are supported
by text or icons rather than being the only status signal.

## Verification

Verify the redesigned PySide6 application at:

- 1366x768;
- 1440x900;
- 1920x1080;
- 2560x1440.

Check:

- Home first-run, recent-project, and runtime-warning states;
- scene editing with mouse and numeric inputs;
- inspector collapse and splitter behavior;
- inline validation navigation;
- Simulation ready and blocked states;
- run monitor running, completed, cancelled, and failed states;
- Results empty, loading, completed, and unreadable-output states;
- RU and EN labels;
- idle CPU behavior;
- interaction latency with larger scenes;
- absence of full scene rebuilds during simple field typing and drag preview.

## Implementation Order

1. Add performance instrumentation and remove full scene rebuilds from simple
   edits.
2. Refine shared shell and design tokens.
3. Implement the approved Home screen.
4. Restructure Model Editor around the scene, layer list, and contextual
   inspector.
5. Simplify Simulation setup and monitor states.
6. Give Results more chart space and compact selectors.
7. Polish Diagnostics, Settings, RU/EN localization, and responsive behavior.
8. Run interaction, state, and viewport verification.

