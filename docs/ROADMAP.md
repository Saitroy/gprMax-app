# Roadmap

## Русский

## Stage 0: Discovery и архитектура

Поставки:

- проанализировать `gprMax` и исторический `gprMax-Designer`;
- определить архитектуру, структуру проекта и начальные technical decisions;
- задокументировать product direction и engineering direction.

Критерии выхода:

- архитектура и integration strategy задокументированы;
- initial decisions сформулированы явно и доступны для review.

## Stage 1: Skeleton и app shell

Поставки:

- layout репозитория и packaging metadata;
- запускаемая PySide6 application shell;
- главное окно со стабильной top-level navigation;
- placeholder views для welcome, model editor, runs, results и settings;
- application context, logging bootstrap и service skeletons.

Критерии выхода:

- desktop app открывается и позволяет переключаться между screens;
- codebase имеет чистую baseline для итеративной разработки.

## Stage 2: Project model, persistence и settings

Поставки:

- versioned project manifest format;
- flows create/open/save, подключённые к UI;
- recent projects с persisted metadata;
- scaffolding структуры директорий проекта;
- typed essential project model, выровненная с docs `gprMax`;
- validation правил уровня persistence;
- persistence application settings.

Критерии выхода:

- пользователь может создавать и повторно открывать проекты без ручной работы с raw files.

## Stage 3: `gprMax` integration layer и runner

Поставки:

- subprocess adapter для `gprMax`;
- input generation service и writer;
- run configuration model;
- stdout/stderr capture с live UI updates;
- run history и per-run metadata manifests;
- validation перед запуском;
- failure reporting и cancellation.

Критерии выхода:

- проект может запускать реальный `gprMax` run из GUI и сохранять artifacts.

## Stage 4: Model Editor MVP

Поставки:

- guided forms для core model parameters;
- materials, waveforms, sources, receivers и focused geometry subset;
- validation и sensible defaults;
- generated input preview;
- wiring с project state, persistence и existing simulation runner.

Критерии выхода:

- непограммист может собрать базовую модель без ручного написания input-файла.

## Stage 5: Results Viewer MVP

Поставки:

- run-centric results browser по проекту и run;
- HDF5 result reader layer;
- metadata summary и visibility artifacts;
- A-scan plotting;
- bounded B-scan preview flow;
- открытие result folder и artifacts из UI.

Критерии выхода:

- пользователь может inspect run outputs и понять, где именно записаны artifacts.

## Stage 6: Advanced mode

Поставки:

- raw input editor и diff/preview с generated input;
- advanced run options;
- более глубокие post-processing и power-user results workflows;
- expert settings без деградации guided flow.

Критерии выхода:

- power users сохраняют широкий контроль над возможностями `gprMax`.

## Stage 7: Packaging и installer

Поставки:

- standalone build pipeline;
- Windows installer;
- первая стратегия bundling/runtime management для `gprMax`.

Критерии выхода:

- новый пользователь может установить и открыть приложение без ручной настройки Python.

## Stage 8: Documentation, tests и release preparation

Поставки:

- developer docs и contributor guidance;
- расширенные unit/integration tests;
- release checklist и baseline CI.

Критерии выхода:

- проект готов к внешним контрибьюторам и early adopters.

## English

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
- input generation service and writer;
- run configuration model;
- stdout/stderr capture with live UI updates;
- run history and per-run metadata manifests;
- validation before launch;
- failure reporting and cancellation.

Exit criteria:

- a project can launch a real `gprMax` run from the GUI and preserve artifacts.

## Stage 4: Model editor MVP

Deliverables:

- guided forms for core model parameters;
- materials, waveforms, sources, receivers, and focused geometry subset;
- validation and sensible defaults;
- generated input preview;
- wiring to project state, persistence, and the existing simulation runner.

Exit criteria:

- non-programmer users can build a basic model without hand-writing input.

## Stage 5: Results viewer MVP

Deliverables:

- run-centric results browser by project and run;
- HDF5 result reader layer;
- metadata summary and artifact visibility;
- A-scan plotting;
- bounded B-scan preview flow;
- open result folder and artifacts from UI.

Exit criteria:

- users can inspect run outputs and identify where artifacts were written.

## Stage 6: Advanced mode

Deliverables:

- raw input editor and diff/preview with generated input;
- advanced run options;
- deeper post-processing and power-user results workflows;
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
# Stage 6

## Русский

- bundled-first runtime foundation;
- engine resolution layer;
- installer-oriented path management;
- runtime diagnostics and capability reporting;
- settings UI as runtime/health screen;
- foundation for future installer and release engineering.

## English

- bundled-first runtime foundation;
- engine resolution layer;
- installer-oriented path management;
- runtime diagnostics and capability reporting;
- settings UI as a runtime/health screen;
- foundation for future installer and release engineering.
