# Screen Specs

Формат: purpose, current implementation, user actions, inputs, outputs, states, UX issues, designer notes.

## Main Window / App Shell

Код: `src/gprmax_workbench/ui/main_window.py`.

Purpose: общий контейнер desktop-приложения, навигация между главными workspace, глобальные команды.

Current implementation:

- `QMainWindow`, menu bar, status bar;
- sidebar `QListWidget`;
- content stack `QStackedWidget`;
- pages wrapped in scroll areas;
- horizontal shell splitter;
- UI state saved on close.

User actions:

- выбрать страницу;
- создать, открыть, сохранить проект;
- открыть settings;
- открыть about;
- работать с диалогами ошибок.

States:

- no project;
- project opened;
- dirty project, marker `*` in window title;
- active run suffix in window title;
- page restored from saved UI state.

UX issues:

- Settings отсутствует в основной навигации;
- нет guard для unsaved changes;
- QScrollArea вокруг всех страниц может создавать nested scroll complexity.

Designer notes:

- определить глобальную IA: sidebar vs top tabs vs command bar;
- сделать active project/run status постоянным и компактным;
- предусмотреть reset layout.

## Welcome

Код: `src/gprmax_workbench/ui/views/welcome_view.py`.

Purpose: первый экран, старт проекта, быстрый возврат к работе.

Current implementation:

- hero card с New/Open/Documentation;
- current workspace status card;
- recent projects list;
- workflow help as tooltip.

User actions:

- New Project;
- Open Project;
- Documentation;
- double click recent project.

Inputs:

- none on screen.

Outputs:

- project status;
- readiness;
- latest activity;
- recent project names/paths.

States:

- empty: no project, no recent projects;
- normal: current project and recent list;
- error: open recent project can fail via `QMessageBox.critical`;
- success: status bar after open/create.

Missing / recommended:

- example/template cards directly on Welcome;
- first-run checklist;
- open example CTA without opening Documentation dialog;
- "what is gprMax" short explanation for novices.

UX issues:

- `_example_projects` stored but not rendered in Welcome;
- hero uses large card styling, but app is an operational tool.

Designer notes:

- Welcome should be a practical command center;
- prioritize New/Open/Recent/Examples/Environment status.

## New Project Dialog

Код: `src/gprmax_workbench/ui/dialogs/new_project_dialog.py`.

Purpose: собрать имя и папку проекта.

Current implementation:

- modal dialog;
- project name `QLineEdit`;
- project directory `QLineEdit`;
- Browse directory;
- OK/Cancel.

Validation:

- empty project name warning;
- empty directory warning.

States:

- normal;
- validation error;
- cancelled;
- success;
- create failure via `QMessageBox.critical`.

Missing / recommended:

- path preview: final project root;
- warning when folder exists and contains files;
- default template selection;
- project description.

## Project Workspace

Код: `src/gprmax_workbench/ui/views/project_view.py`.

Purpose: основная рабочая область для редактирования модели.

Current implementation:

- project info card;
- save button;
- section toolbar buttons;
- stacked sections;
- advanced section hidden when advanced mode is off.

User actions:

- save project;
- switch sections;
- edit model in child panels.

Inputs:

- all model data through child panels.

Outputs:

- project root;
- manifest path;
- entity counts;
- validation summary;
- workflow hint.

States:

- no project;
- dirty;
- saved;
- validation warnings;
- validation errors;
- advanced off/on.

UX issues:

- section toolbar can become visually dense;
- hidden nav card exists but is not used;
- save errors appear in message box, not as actionable section links.

Designer notes:

- design a scalable section navigation;
- group model setup by workflow, not only data type;
- make validation summary navigable.

## Scene

Код: `src/gprmax_workbench/ui/widgets/model_editor/scene_canvas_panel.py`.

Purpose: visual editor for model composition.

Current implementation:

- QGraphics canvas;
- plane switch XY/XZ/YZ;
- select/create/measure tools;
- move/resize modes;
- snap/grid controls;
- layer filters;
- labels toggle;
- undo/redo;
- fit scene;
- palette: box, sphere, cylinder, source, receiver, antenna, import;
- right side scroll panel;
- inspector for position and entity-specific fields;
- entity list;
- model status summary.

User actions:

- drag palette entity to canvas;
- add entity at center;
- right-click create;
- select/multi-select;
- move/resize;
- nudge;
- duplicate/delete;
- edit exact coordinates;
- switch to detailed section.

Inputs:

- domain size;
- entity positions;
- geometry size/radius/material;
- source axis/waveform;
- receiver outputs;
- grid/nudge step.

Outputs:

- visual spatial layout;
- rulers;
- cursor coordinates;
- zoom;
- model summary;
- validation messages.

States:

- no project;
- empty scene;
- normal;
- selected item;
- multi-selected;
- create mode;
- measure mode;
- resize mode;
- validation warning/error;
- history undo/redo available/disabled.

UX issues:

- very high control density;
- side panel combines guide, domain, palette, inspector, entity list and status;
- delete has no confirmation;
- toolbar compact mode hides labels/status on small widths, but still needs design validation.

Designer notes:

- separate primary canvas actions from secondary inspector actions;
- make advanced layers/settings collapsible;
- use visual chips/status for object counts and validation;
- preserve keyboard workflows but avoid relying on hidden shortcuts.

## Domain / Grid / Time Window

Код: `src/gprmax_workbench/ui/widgets/model_editor/general_panel.py`.

Purpose: metadata and core calculation domain.

Current implementation:

- metadata group;
- domain group;
- fixed-height notes fields;
- status label.

Inputs:

- project name;
- description;
- model title;
- model notes;
- tags;
- domain size X/Y/Z;
- resolution X/Y/Z;
- time window;
- scan trace count.

Outputs:

- validation status.

States:

- disabled/no project;
- normal;
- validation errors;
- validation warnings.

Missing / recommended:

- PML controls;
- derived grid cells and estimated workload;
- unit explanation.

## Materials

Код: `src/gprmax_workbench/ui/widgets/model_editor/materials_panel.py`.

Purpose: define media/material properties.

Current implementation:

- presets;
- list-detail layout;
- swatch preview;
- usage count.

Inputs:

- identifier;
- relative permittivity;
- conductivity;
- relative permeability;
- magnetic loss;
- notes;
- tags.

Actions:

- add;
- duplicate;
- delete;
- apply preset.

States:

- empty;
- selected material;
- validation error;
- no project/disabled.

UX issues:

- material delete has no dependency warning despite usage count;
- units and geophysical meaning need clearer labels/tooltips.

## Waveforms

Код: `src/gprmax_workbench/ui/widgets/model_editor/waveforms_panel.py`.

Purpose: define source signal shapes.

Inputs:

- identifier;
- kind;
- amplitude;
- center frequency;
- notes;
- tags.

Actions:

- add, duplicate, delete.

States:

- empty;
- selected;
- validation error;
- no project.

Designer notes:

- designers should add waveform preview/sparkline as recommended future component.

## Sources

Код: `src/gprmax_workbench/ui/widgets/model_editor/sources_panel.py`.

Purpose: configure excitation points.

Inputs:

- identifier;
- source kind;
- axis;
- waveform;
- position;
- delay;
- resistance for voltage source;
- notes/tags.

Actions:

- add, duplicate, delete.

States:

- no waveform available;
- selected;
- voltage source with resistance enabled;
- other source with resistance disabled;
- validation warnings/errors.

UX issues:

- waveform dependency is a combo, but missing waveform state needs stronger guidance.

## Receivers

Код: `src/gprmax_workbench/ui/widgets/model_editor/receivers_panel.py`.

Purpose: configure output measurement points.

Inputs:

- identifier;
- position;
- output components as CSV text;
- notes/tags.

Actions:

- add, duplicate, delete.

States:

- empty;
- selected;
- invalid position;
- no project.

Missing / recommended:

- component selector instead of free text CSV;
- receiver array guided UI.

## Geometry

Код: `src/gprmax_workbench/ui/widgets/model_editor/geometry_panel.py`.

Purpose: detailed form editor for geometry primitives.

Inputs:

- label;
- kind;
- material;
- dielectric smoothing;
- parameters by kind;
- notes/tags.

Actions:

- add, duplicate, delete.

States:

- empty;
- selected box/sphere/cylinder;
- validation error;
- unknown material warning.

UX issues:

- separate from Scene, so users may be unsure where to edit geometry;
- material required but not visually marked as required.

## Libraries / Imports

Код: `src/gprmax_workbench/ui/widgets/model_editor/libraries_panel.py`.

Purpose: imported geometry and antenna model setup.

Current implementation:

- `QTabWidget` with Geometry import and Antennas.

Geometry import inputs:

- identifier;
- HDF5 geometry file;
- materials file;
- position;
- smoothing;
- notes/tags.

Antennas inputs:

- identifier;
- library/model;
- Python module/function;
- position;
- resolution;
- rotate 90;
- notes/tags.

States:

- no selected import/antenna;
- file exists/missing preview;
- catalog/default;
- custom model;
- validation warning/error.

UX issues:

- file missing is text-only;
- Python module/function may scare non-programmers.

Designer notes:

- catalog-first UI for antennas;
- custom module behind advanced disclosure;
- file status as visual badge.

## Advanced Commands

Код: `src/gprmax_workbench/ui/widgets/model_editor/advanced_panel.py`.

Purpose: raw gprMax/Python escape hatch.

Inputs:

- category;
- template;
- raw commands text;
- Python blocks text.

Actions:

- insert template;
- insert Python block;
- move/delete blocks;
- apply changes.

States:

- hidden by default;
- no project;
- normal editing;
- applied;
- validation text.

UX issues:

- not suitable for novice users;
- block model is text-based;
- no detailed syntax errors except highlighter and generated validation.

Designer notes:

- advanced mode should be clearly separated and reversible;
- technical copy should not leak into primary workflow.

## Input Preview

Код: `src/gprmax_workbench/ui/widgets/model_editor/preview_panel.py`.

Purpose: show generated gprMax input from current model.

Actions:

- rebuild preview;
- export preview.

Outputs:

- validation/preflight messages;
- generated input text.

States:

- empty;
- normal preview;
- export success;
- no project.

UX issue:

- duplicates Simulation Preview concept; designers should decide whether preview belongs in Project, Simulation, or both with different purpose.

## Simulation / Launch

Код: `src/gprmax_workbench/ui/views/simulation_view.py`.

Purpose: preflight and run configuration.

Inputs:

- run mode;
- number of runs;
- geometry fixed;
- write processed;
- advanced: restart, MPI tasks, benchmark, MPI no spawn, extra args.

Actions:

- Start;
- Retry;
- Preview;
- Export;
- Cancel;
- Open Run Folder;
- Open Output Folder.

Outputs:

- readiness;
- runtime;
- project state;
- run state;
- validation/runtime messages;
- metrics.

States:

- no project;
- not ready;
- ready;
- busy;
- running;
- completed;
- failed/cancelled.

UX issues:

- no progress visualization;
- CPU/GPU not represented;
- advanced rows are hidden, but no visible "advanced mode is off" hint.

## Simulation / Preview

Код: `src/gprmax_workbench/ui/views/simulation_view.py`.

Purpose: inspect run-ready input generated with the current run configuration.

Outputs:

- read-only generated input.

States:

- empty placeholder;
- preview loaded;
- error via message box.

Designer notes:

- show generated input as secondary technical details for most users.

## Simulation / Logs

Код: `src/gprmax_workbench/ui/views/simulation_view.py`.

Purpose: live run diagnostics and run history.

Outputs:

- combined stdout/stderr;
- run history list.

States:

- no logs;
- running live logs;
- completed logs;
- failed logs;
- selected past run.

UX issues:

- stdout/stderr are combined with prefixes, not separated by user-friendly summary;
- no filtering/search/copy support in UI.

## Results

Код: `src/gprmax_workbench/ui/views/results_view.py`.

Purpose: run-centric result browser.

Actions:

- refresh;
- open output directory;
- open selected file;
- choose run;
- choose A-scan/B-scan selectors.

Inputs:

- run selection;
- output file selection;
- receiver/component selection.

Outputs:

- run metadata;
- output/artifact lists;
- A-scan chart;
- B-scan image;
- status messages.

States:

- open project first;
- no results;
- select run;
- no output files;
- unreadable file;
- loaded A-scan;
- unavailable B-scan;
- loaded B-scan.

UX issues:

- no export/report/compare;
- no visible loading state;
- chart controls missing.

## Settings

Код: `src/gprmax_workbench/ui/views/settings_view.py`.

Purpose: app preferences and runtime diagnostics.

Inputs:

- language;
- external runtime executable;
- advanced mode.

Outputs:

- runtime summary;
- capability status;
- diagnostics.

States:

- runtime healthy/unhealthy;
- advanced mode off/on;
- external runtime path disabled/enabled;
- diagnostics empty or populated.

UX issues:

- no Browse button for executable;
- no Check/Refresh Environment action;
- no theme settings despite product requirement;
- not in main navigation.

## Documentation Dialog

Код: `src/gprmax_workbench/ui/dialogs/documentation_dialog.py`.

Purpose: open docs/examples and launch example projects.

Actions:

- open README;
- open docs folder;
- open examples folder;
- open example project.

States:

- examples available;
- examples none.

UX issue:

- examples are one click deeper than Welcome.

