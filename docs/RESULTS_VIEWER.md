# Results Viewer MVP

## Русский

## Scope

Stage 5 вводит run-centric Results Viewer MVP.

Сейчас поддерживается:

- просмотр completed и incomplete runs через persisted metadata;
- discovery `.out` files и auxiliary visualisation artifacts;
- чтение HDF5 result metadata через выделенный reader layer;
- список receivers и доступных output components;
- A-scan plotting внутри desktop-приложения;
- bounded B-scan preview из:
  - merged output file, если он есть; или
  - нескольких single-trace `.out` files с совместимым receiver/component layout.

Сознательно отложено:

- полноценные scientific post-processing suites;
- FFT/spectral views;
- embedded geometry/snapshot viewers;
- advanced multi-run comparison dashboards;
- прямой support всех plotting utilities `gprMax`.

## UX structure

Results Viewer использует run-centric layout:

- слева: run navigator;
- справа сверху: run/result summary;
- справа по центру: output files и other artifacts;
- справа снизу: receiver/component selectors и tabs `A-scan` / `B-scan`.

Почему так:

- пользователи сначала думают о run, а не о low-level file structure;
- основные вопросы: «run завершился?», «какие outputs есть?», «можно ли сейчас посмотреть trace?»;
- layout остаётся совместимым с будущими viewer tabs без полного редизайна окна.

## Reading strategy

UI не читает HDF5 files напрямую.

Вместо этого:

1. `ResultArtifactLocator` находит result candidates в run folder.
2. `Hdf5ResultsReader` читает typed metadata и trace data.
3. `ResultRepository` отдаёт эти чтения в application-facing operations.
4. `ResultsService`, `TraceService` и `BscanService` координируют viewer workflows.

Это изолирует file-format handling от Qt widgets и делает этап тестируемым без live `gprMax` runtime.

## Границы B-scan MVP

B-scan support на Stage 5 намеренно ограничен.

Поддерживается:

- merged output files, когда dataset выбранного receiver/component двумерный;
- stacked previews из нескольких single-trace `.out` files, когда длины traces совместимы.

Пока не поддерживается:

- произвольные merge workflows со сложным preprocessing;
- advanced sampling/position controls;
- rich scientific color-mapping и export pipelines.

Если B-scan недоступен, UI явно объясняет причину, а не молча ломается.

## English

## Scope

Stage 5 introduces a run-centric Results Viewer MVP.

Supported now:

- browsing completed and incomplete runs through their persisted metadata;
- discovering `.out` files and auxiliary visualisation artifacts;
- reading HDF5 result metadata behind a dedicated reader layer;
- listing receivers and available output components;
- plotting A-scan traces inside the desktop app;
- building a bounded B-scan preview from:
  - a merged output file when present; or
  - multiple single-trace `.out` files with compatible receiver/component layouts.

Deferred intentionally:

- full scientific post-processing suites;
- FFT/spectral views;
- geometry/snapshot embedded viewers;
- advanced multi-run comparison dashboards;
- direct support for every `gprMax` plotting utility.

## UX structure

The Results Viewer uses a run-centric layout:

- left: run navigator;
- right top: run/result summary;
- right middle: output files and other artifacts;
- right lower: receiver/component selectors with A-scan and B-scan tabs.

Why this shape:

- users think in terms of runs first, not low-level files first;
- the most common questions are: "Did the run finish?", "What outputs exist?", and "Can I inspect a trace now?";
- the layout stays compatible with future viewer tabs without redesigning the whole window.

## Reading strategy

The UI does not read HDF5 files directly.

Instead:

1. `ResultArtifactLocator` finds result candidates from the run folder.
2. `Hdf5ResultsReader` reads typed metadata and trace data.
3. `ResultRepository` exposes those reads as application-facing operations.
4. `ResultsService`, `TraceService`, and `BscanService` coordinate viewer workflows.

This keeps file format handling isolated from Qt widgets and makes the stage testable without a live `gprMax` runtime.

## B-scan MVP boundary

The Stage 5 B-scan support is intentionally bounded.

Supported:

- merged output files when the selected receiver/component dataset is 2D;
- stacked previews from multiple single-trace `.out` files when trace lengths are consistent.

Unsupported for now:

- arbitrary merge workflows with complex preprocessing requirements;
- advanced sampling/position controls;
- rich scientific color-mapping and export pipelines.

When B-scan is unavailable, the UI says why instead of silently failing.
