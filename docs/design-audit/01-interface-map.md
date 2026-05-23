# Interface Map

## UI source map

Основные UI-файлы:

| Зона | Код | Назначение |
|---|---|---|
| App entry/context | `src/gprmax_workbench/app.py` | Создает сервисы, runtime, `MainWindow`, применяет тему |
| Main window | `src/gprmax_workbench/ui/main_window.py` | Главное окно, меню, sidebar, page stack, dialogs, handlers |
| Theme | `src/gprmax_workbench/ui/theme.py` | Глобальный stylesheet |
| Welcome | `src/gprmax_workbench/ui/views/welcome_view.py` | Стартовый экран |
| Project | `src/gprmax_workbench/ui/views/project_view.py` | Рабочая зона редактора модели |
| Simulation | `src/gprmax_workbench/ui/views/simulation_view.py` | Настройка и мониторинг запуска |
| Results | `src/gprmax_workbench/ui/views/results_view.py` | Просмотр run outputs, A-scan/B-scan |
| Settings | `src/gprmax_workbench/ui/views/settings_view.py` | Настройки, runtime summary, diagnostics |
| New Project dialog | `src/gprmax_workbench/ui/dialogs/new_project_dialog.py` | Создание проекта |
| Settings dialog | `src/gprmax_workbench/ui/dialogs/settings_dialog.py` | Немодальное окно настроек |
| Documentation dialog | `src/gprmax_workbench/ui/dialogs/documentation_dialog.py` | Документация, examples |
| Model editor widgets | `src/gprmax_workbench/ui/widgets/model_editor/*.py` | Секции редактора модели |
| Results widgets | `src/gprmax_workbench/ui/widgets/results/*.py` | Summary, A-scan chart, B-scan image |

Неиспользованные или неинтегрированные UI-заготовки:

- `src/gprmax_workbench/ui/widgets/workspace_banner.py` - готовый context/banner widget, но в `MainWindow` или views не подключен.
- `QTreeWidget#ProjectExplorer` стилизован в `theme.py`, но фактический `QTreeWidget` project explorer не найден.

## App shell

Код: `src/gprmax_workbench/ui/main_window.py`.

Текущая структура:

- `QMainWindow`;
- `QMenuBar`: File, Settings, Help;
- `QStatusBar`;
- `QSplitter` horizontal;
- left sidebar `QListWidget#Navigation`;
- content `QStackedWidget`;
- каждая page завернута в `QScrollArea#PageScrollArea`.

Размеры:

- initial resize: `1440 x 920`;
- minimum: `920 x 680`;
- adaptive resize при старте: целевой размер зависит от `screen.availableGeometry()`;
- sidebar: `210..280 px`.

Главные страницы в `PageSpec`:

1. Welcome.
2. Project.
3. Simulation.
4. Results.

Settings не входит в `PageSpec`. Он открывается через меню как `SettingsDialog`.

## Global menu and actions

Код: `MainWindow._create_actions()`.

| Menu | Action | Handler | UI effect |
|---|---|---|---|
| File | New Project | `_on_new_project()` | Открывает `NewProjectDialog`, создает project root |
| File | Open Project | `_on_open_project()` | Directory picker, затем open project |
| File | Save Project | `_on_save_project()` | Сохраняет manifest, показывает warnings/errors |
| Settings | Open Settings | `_open_settings_page()` | Показывает `SettingsDialog` |
| Help | About | `_show_about_dialog()` | `QMessageBox.information` |

Missing / recommended:

- prompt при несохраненных изменениях перед New/Open/Close;
- recent projects в меню File;
- quick links на project folder, support bundle, diagnostics;
- отдельный Help action для Documentation, сейчас Documentation доступна через Welcome.

## Welcome

Код: `src/gprmax_workbench/ui/views/welcome_view.py`.

Состав:

- заголовок и subtitle;
- info button с workflow tooltip;
- hero card;
- primary action: New Project;
- secondary action: Open Project;
- documentation action;
- status card: current project, readiness, activity;
- recent projects list.

Данные:

- current project из `WorkspaceService.state.current_project`;
- recent projects из `SettingsService`;
- readiness/activity summary из `MainWindow._refresh_welcome_summary()`.

Examples:

- `MainWindow._discover_example_projects()` читает `examples/summary.json`;
- список передается в `WelcomeView.set_example_projects()`;
- в `WelcomeView` список не отрисовывается;
- реальные кнопки examples создаются в `DocumentationDialog.set_examples()`.

## Project workspace

Код: `src/gprmax_workbench/ui/views/project_view.py`.

Состав верхнего уровня:

- title/subtitle;
- project summary card: root, manifest path, summary, validation, workflow hint, Save Project;
- section toolbar card: кнопки секций через `FlowLayout`;
- hidden nav card `QListWidget#ContextNavigation`, сейчас `self._nav_card.setVisible(False)`;
- `QStackedWidget` секций.

Секции Project:

| Section key | Widget | Код | Advanced mode |
|---|---|---|---|
| `project.section.scene` | Scene | `scene_canvas_panel.py` | visible |
| `project.section.area` | General/domain | `general_panel.py` | visible |
| `project.section.materials` | Materials | `materials_panel.py` | visible |
| `project.section.signal` | Waveforms | `waveforms_panel.py` | visible |
| `project.section.sources` | Sources | `sources_panel.py` | visible |
| `project.section.receivers` | Receivers | `receivers_panel.py` | visible |
| `project.section.geometry` | Geometry | `geometry_panel.py` | visible |
| `project.section.libraries` | Libraries/imports | `libraries_panel.py` | visible |
| `project.section.advanced` | Advanced commands | `advanced_panel.py` | hidden unless advanced mode |
| `project.section.preview` | Input preview | `preview_panel.py` | visible |

Service connections:

- all edit panels mutate via `ModelEditorService`;
- validation read via `ValidationService`;
- input preview via `InputPreviewService`;
- save via `MainWindow._on_save_project()`.

## Scene canvas

Код: `src/gprmax_workbench/ui/widgets/model_editor/scene_canvas_panel.py`.

Состав:

- `QGraphicsScene` + custom `_CanvasView`;
- metric rulers;
- toolbar with plane, tool, mode, layers, history, cursor status, zoom, fit scene;
- side scroll panel with guide, snap/grid controls, domain size, palette, inspector, entity list, validation status;
- workspace splitter between canvas and side panel.

Canvas features:

- planes: XY, XZ, YZ;
- tools: Select, Create, Measure;
- modes: Move, Resize;
- snap to grid;
- layer visibility: geometry, source, receiver, other;
- labels on/off;
- drag/drop palette;
- right-click context menu on entity: edit, duplicate, delete;
- right-click context menu on empty canvas: add box/sphere/cylinder/source/receiver/antenna/import;
- multi-select;
- nudge buttons;
- undo/redo via `ModelEditorService`.

Entities displayed:

- geometry primitives;
- sources;
- receivers;
- antenna models;
- imported geometry.

## General / Domain

Код: `src/gprmax_workbench/ui/widgets/model_editor/general_panel.py`.

Groups:

- metadata: project name, description, model title, model notes, tags;
- domain: size X/Y/Z, resolution X/Y/Z, time window, scan trace count.

Validation prefixes:

- `metadata`;
- `model.title`;
- `model.domain`;
- `model.scan_trace_count`.

Missing / recommended:

- guided PML editor;
- unit hints and derived values, for example grid cells count;
- inline warnings for extremely heavy meshes.

## Materials

Код: `src/gprmax_workbench/ui/widgets/model_editor/materials_panel.py`.

Состав:

- presets card: air, dry sand, wet soil, concrete, fresh water;
- list-detail editor;
- material swatch and usage count;
- fields: identifier, relative permittivity, conductivity, relative permeability, magnetic loss, notes, tags;
- add, duplicate, delete.

## Waveforms

Код: `src/gprmax_workbench/ui/widgets/model_editor/waveforms_panel.py`.

Fields:

- identifier;
- kind: `ricker`, `gaussian`, `gaussiandot`, `gaussiandotnorm`;
- amplitude;
- center frequency;
- notes;
- tags.

Actions:

- add, duplicate, delete.

## Sources

Код: `src/gprmax_workbench/ui/widgets/model_editor/sources_panel.py`.

Fields:

- identifier;
- kind: `hertzian_dipole`, `magnetic_dipole`, `voltage_source`;
- axis: x/y/z;
- waveform reference;
- position X/Y/Z;
- delay;
- resistance for voltage source;
- notes;
- tags.

## Receivers

Код: `src/gprmax_workbench/ui/widgets/model_editor/receivers_panel.py`.

Fields:

- identifier;
- position X/Y/Z;
- outputs as CSV text, for example `Ez`;
- notes;
- tags.

## Geometry

Код: `src/gprmax_workbench/ui/widgets/model_editor/geometry_panel.py`.

Fields:

- label;
- kind: box, sphere, cylinder;
- material;
- dielectric smoothing;
- kind-specific parameters;
- notes;
- tags.

Parameter stacks:

- box: lower-left X/Y/Z, upper-right X/Y/Z;
- sphere: center X/Y/Z, radius;
- cylinder: start X/Y/Z, end X/Y/Z, radius.

## Libraries and import

Код: `src/gprmax_workbench/ui/widgets/model_editor/libraries_panel.py`.

Tabs:

1. Geometry import.
2. Antennas.

Geometry import:

- identifier;
- geometry HDF5 file with file picker;
- materials file with file picker;
- position X/Y/Z;
- dielectric smoothing;
- notes/tags;
- text preview of generated `#geometry_objects_read`.

Antennas:

- identifier;
- library;
- model;
- module;
- function;
- position X/Y/Z;
- base resolution;
- rotate 90 degrees;
- notes/tags;
- catalog summary;
- Python preview.

Current catalog:

- `gprmax_user_libs/gssi_1500`;
- `gprmax_user_libs/gssi_400`;
- `gprmax_user_libs/mala_1200`.

## Advanced commands

Код: `src/gprmax_workbench/ui/widgets/model_editor/advanced_panel.py`.

Visible only when advanced mode is enabled in Settings.

Состав:

- category combo;
- command template list;
- template preview;
- insert template;
- insert Python block;
- tabbed editors: raw gprMax commands, Python blocks;
- block lists for both editors;
- move up/down/delete block;
- apply advanced changes.

Command categories from registry:

- general;
- materials;
- objects;
- imports;
- sources;
- outputs;
- pml.

## Input Preview

Код: `src/gprmax_workbench/ui/widgets/model_editor/preview_panel.py`.

Состав:

- title;
- Rebuild Preview;
- Export;
- messages text area;
- generated input text area.

Отдельно в Simulation есть свой input preview/export flow. Это потенциальное дублирование UX.

## Simulation

Код: `src/gprmax_workbench/ui/views/simulation_view.py`.

Верхний уровень:

- title/subtitle;
- action bar: Start, Retry, Preview, Export, Cancel, Open Run Folder, Open Output Folder;
- section nav `QListWidget#ContextNavigation`;
- section stack.

Sections:

1. Launch.
2. Input preview.
3. Logs.

Launch:

- metric tiles: readiness, mode, runs, activity;
- status card: runtime, readiness, project state, run state, messages;
- config card: mode, number of model runs, geometry fixed, write processed;
- advanced rows: restart, MPI tasks, benchmark, MPI no spawn, extra args.

Logs:

- combined live log text;
- run history list.

Missing / recommended:

- progress bar, stages, ETA;
- GPU controls;
- separate diagnostics action near readiness;
- structured stdout/stderr separation for normal users.

## Results

Код: `src/gprmax_workbench/ui/views/results_view.py`.

Верхний уровень:

- toolbar: Refresh, Open Output Folder, Open Selected File;
- vertical splitter: plot area above, run/details below;
- bottom splitter: run list left, summary/artifacts right;
- tabs in plot area: A-scan, B-scan.

A-scan:

- output combo;
- optional "show individual A-scan traces";
- receiver combo;
- component checklist;
- `TracePlotWidget` with Qt Charts;
- status label.

B-scan:

- output combo;
- receiver combo;
- component combo;
- `BscanImageWidget`;
- status label.

Summary:

- run id, status, created/finished, duration;
- input file;
- output file;
- model title;
- receivers;
- components;
- grid;
- dt;
- notes/issues.

Missing / recommended:

- export image/data/report;
- compare runs;
- plot settings;
- color scale controls;
- loading indicator while reading HDF5.

## Settings

Код:

- `src/gprmax_workbench/ui/views/settings_view.py`;
- `src/gprmax_workbench/ui/dialogs/settings_dialog.py`.

Fields:

- language selector;
- external gprMax Python executable path;
- advanced mode toggle;
- runtime summary;
- capabilities summary;
- diagnostics summary.

Important behavior:

- runtime executable field is disabled until advanced mode is enabled;
- capabilities omit `gpu` in current UI display;
- settings are saved through `SettingsService.update_preferences()`.

Missing / recommended:

- file picker for runtime executable;
- explicit "check environment" button;
- theme settings;
- performance/export settings;
- reset UI layout.

## Dialogs and message boxes

Custom dialogs:

- `NewProjectDialog`: project name, project directory, Browse, OK/Cancel.
- `SettingsDialog`: non-modal wrapper around `SettingsView`.
- `DocumentationDialog`: open README/docs/examples folder, open example projects.

Native dialogs:

- directory picker for open project;
- save file picker for simulation input export;
- save file picker for model editor preview export;
- open file picker for geometry/materials imports;
- message boxes for errors, warnings, info, about.

Missing / recommended:

- confirmation dialog before delete;
- confirmation before losing unsaved changes;
- richer error dialog with "simple message" and collapsible technical details.

