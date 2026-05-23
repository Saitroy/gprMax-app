# UI Components

## Navigation components

Current:

- Main sidebar: `QListWidget#Navigation` in `MainWindow`.
- Project section toolbar: `FlowLayout` of checkable `QPushButton`.
- Simulation section navigation: `QListWidget#ContextNavigation`.
- Results tabs: `QTabWidget` for A-scan/B-scan.
- Libraries tabs: `QTabWidget` for imports/antennas.
- Advanced tabs: `QTabWidget` for raw commands/Python.

Designer guidance:

- keep one primary navigation model;
- avoid two competing section navigations in Project;
- make active state strong but quiet;
- reserve tabs for peer views, not full workflow steps if side navigation is used.

## Buttons and actions

Primary buttons:

- Welcome New Project;
- Simulation Start;
- Settings Save.

Secondary buttons:

- Open Project;
- Documentation;
- Save Project;
- Add/Duplicate/Delete;
- Preview/Export;
- Retry/Cancel/Open folders;
- Browse file/folder.

Problems:

- many text buttons in dense tool areas;
- destructive Delete has no confirmation;
- icon usage is inconsistent and mostly default Qt icons in Scene.

Recommended components:

- primary CTA;
- secondary button;
- destructive button;
- icon button with tooltip;
- split button/menu for advanced actions;
- disabled button with reason tooltip.

## Forms and inputs

Current input types:

- `QLineEdit` for names, identifiers, tags, paths, outputs, extra args;
- `QPlainTextEdit` for descriptions, notes, logs, preview text;
- `QSpinBox` for counts;
- `QDoubleSpinBox` via `build_float_spinbox()` for physical values;
- `QComboBox` for modes/kinds/references;
- `QCheckBox` for toggles;
- file/folder dialogs.

Key form domains:

- project metadata;
- domain dimensions/resolution/time;
- materials;
- waveforms;
- sources;
- receivers;
- geometry;
- imports/antennas;
- run configuration;
- settings.

Recommended improvements:

- required markers;
- inline validation;
- units displayed consistently;
- field helper text;
- derived values, for example cells count and estimated workload;
- CSV outputs replaced by checklist/multi-select.

## Lists and list-detail editors

Current list-detail sections:

- Materials;
- Waveforms;
- Sources;
- Receivers;
- Geometry;
- Geometry imports;
- Antennas;
- Run history;
- Result runs;
- Artifacts;
- Advanced block lists.

Patterns:

- left list;
- right form;
- Add/Duplicate/Delete actions;
- selection drives detail form.

UX issues:

- empty states are often just disabled forms/status text;
- delete is immediate;
- list items are mostly plain text, not structured rows with status badges.

Recommended components:

- entity list item with type, name, status, short metadata;
- empty state with Add action;
- confirmation or undo toast for destructive actions;
- search/filter for longer lists.

## Cards and panels

Current:

- `QFrame#ViewCard` used heavily;
- Welcome hero/status/recent cards;
- Project summary and section toolbar cards;
- Materials preset/preview cards;
- Scene guide/domain/palette/inspector/entities cards;
- Simulation status/config/history cards;
- Results run/summary/artifact/plot cards.

UX issue:

- card density can make operational screens feel visually heavy.

Designer guidance:

- use cards for discrete repeated or framed content;
- avoid nesting many cards in side panels;
- keep operational tools dense but readable.

## Splitters and scroll areas

Current:

- Main shell splitter;
- Project content splitter, with hidden nav card;
- Scene workspace splitter;
- Simulation top/content splitters;
- Results page/bottom splitters;
- Model entity list-detail splitters.

Scroll:

- every main page is wrapped in `QScrollArea`;
- Scene side panel is a separate `QScrollArea`;
- long lists have internal scrolling.

Designer guidance:

- define min/max sizes for major regions;
- avoid nested scroll surprises;
- specify collapsible side panels for 1366x768;
- provide reset layout action.

## Scene canvas components

Current:

- custom graphics view/canvas;
- rulers;
- grid;
- zoom status;
- cursor coordinates;
- palette buttons;
- layer buttons;
- labels;
- selection handles;
- context menus.

Recommended design components:

- canvas toolbar;
- object palette;
- inspector;
- mini model-status strip;
- layer popover;
- measurement overlay;
- empty canvas onboarding.

## Status, validation and messages

Current:

- status labels inside panels;
- Project validation summary;
- Simulation readiness messages;
- Results status labels;
- `QMessageBox` for blocking warnings/errors;
- status bar for success/info.

Problems:

- error messages mix user-level and technical details;
- validation paths like `model.sources[0].waveform_id` can leak to users;
- fields are not inline-highlighted.

Recommended components:

- inline field error;
- section error badge;
- global validation drawer;
- toast/snackbar for success;
- error dialog with short message plus collapsible technical details;
- copy diagnostics action.

## Logs

Current:

- Simulation logs are read-only `QPlainTextEdit`;
- stdout/stderr are combined with prefixes;
- Settings diagnostics are multiline labels.

Recommended components:

- user summary above raw logs;
- tabs or filters: All, Warnings, Errors, Technical;
- copy logs;
- open log file;
- advanced/debug mode for raw logs.

## Charts and visualization

Current:

- A-scan via Qt Charts `QChart`, `QLineSeries`, time axis in ns, amplitude axis;
- B-scan via custom image widget with generated color image, axes, grid, trace number and time axis.

Missing / recommended:

- zoom/pan/reset controls;
- export image;
- export CSV;
- color map and range controls for B-scan;
- compare traces/runs;
- cursor readout.

## Dialogs and modals

Current:

- New Project: modal;
- Settings: non-modal;
- Documentation: non-modal;
- native file/folder pickers;
- message boxes.

Missing / recommended:

- confirm delete;
- unsaved changes;
- environment setup wizard;
- import warnings;
- export success with destination action.

## Theme and visual language

Current theme:

- light blue/grey palette;
- Segoe UI and Bahnschrift;
- rounded cards/buttons;
- custom scrollbar and splitter styles.

Designer requirement:

- move toward clean, modern, Google-like minimal UI;
- reduce visual weight;
- use restrained hierarchy;
- avoid one-note blue/grey dominance if redesign expands the system.

