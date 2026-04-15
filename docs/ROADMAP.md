# GPRMax Workbench Roadmap

## Русский

### Видение

`GPRMax Workbench` должен стать современным Desktop-редактором для gprMax, рассчитанным на геологов, геофизиков, инженеров и студентов, а не на программистов. Пользователь должен скачать installer, установить приложение и сразу собрать модель, запустить расчёт и посмотреть результат без установки Python, Anaconda, репозиториев и ручной настройки зависимостей.

Исторический ориентир: [tomsiwek/gprMax-Designer](https://github.com/tomsiwek/gprMax-Designer). В нём уже была правильная идея визуального редактора модели: toolbar, рабочая область, режимы draw/move/resize, список фигур, RMB-действия, импорт input и parse-to-gprMax. Но его слабое место для массового пользователя очевидно: установка через Python/Anaconda/clone/env/run, отсутствие готовых релизов и устаревший UX. Наша задача не просто повторить его, а сделать лучше.

### Принципы продукта

- Installer-first: пользователь не ставит Python, Anaconda, gprMax и зависимости вручную.
- Visual-first: основная модель собирается на сцене, как в хороших CAD/GIS/визуальных редакторах.
- Precision-first: визуальные действия всегда имеют числовой инспектор, координаты, размеры, материалы и проверку.
- Safe editing: undo/redo, preview перед изменением, понятные подсказки и защита от случайных действий.
- Scientific traceability: каждый run хранит input, параметры запуска, версию runtime, логи и результаты.
- Beginner-friendly, expert-capable: студент не теряется, а опытный геофизик не упирается в потолок.

### Что должно быть лучше, чем в gprMax-Designer

- Установка: один Windows installer вместо ручной сборки окружения.
- Сцена: слои, подписи, фильтры видимости, точное редактирование, multi-select и нормальный инспектор.
- Материалы: понятная библиотека сред, presets, предпросмотр параметров и связь материалов с объектами.
- Валидация: ошибки объясняются до запуска, не после падения gprMax.
- Запуск: preflight, история запусков, cancel/retry/rerun, понятные логи.
- Результаты: A-scan/B-scan анализ внутри приложения, сравнение runs, экспорт для отчётов.
- Поддержка: issue templates, crash/log bundle, sample projects и короткие сценарии для тестеров.

### Alpha 0.2.x: Scene and Materials UX

Цель: сделать редактирование модели визуально понятным и безопасным для первых тестеров.

- Сцена показывает реальные элементы модели, а не формальные фигуры.
- Подписи объектов можно включать и выключать.
- Слои сцены можно фильтровать: объекты, источники, приёмники, прочее.
- Состояние модели видно прямо в редакторе: материалы, объекты, источники, приёмники, warnings/errors.
- Материалы среды выглядят как понятная библиотека/palette, а не как таблица для программиста.
- README и release notes ведут пользователей в GitHub Issues, а не в личную почту.

Exit criteria:

- тестер может открыть приложение, создать простую модель, понять что находится на сцене и где это редактируется;
- типовая жалоба “интерфейс странно себя ведёт” превращается в конкретные UX-issue, а не в растерянность;
- scene editor покрыт unit-тестами на основные пользовательские действия.

### Alpha 0.3: Installer-first Public Testing

Цель: убрать “танцы с бубнами” вокруг установки.

- Windows installer устанавливает приложение и runtime без ручных шагов.
- First-run diagnostics проверяет bundled runtime, writable paths, disk space и базовые capabilities.
- Settings показывают понятный статус: bundled/external runtime, пути, версии, проблемы.
- Release assets публикуются чисто: installer, checksums, release notes RU/EN, known issues.
- Smoke-test installer на чистой Windows VM или максимально близкой тестовой среде.

Exit criteria:

- рядовой геофизик устанавливает приложение без Git, Python, Anaconda и CLI;
- если runtime сломан, приложение объясняет проблему человеческим языком;
- alpha-тестеры получают один понятный файл установки и понятную инструкцию.

### Alpha 0.4: Scene Editor V1

Цель: приблизиться к уровню удобного CAD/GIS-like редактора, сохраняя простоту.

- Полный undo/redo для create/move/resize/delete/duplicate/material changes.
- Multi-select, group move, group duplicate, group delete, marquee selection.
- Layer panel: visibility, labels, lock, select-only по типам объектов.
- Snapping: grid, endpoints, centers, axis lock, numerical nudge.
- Slice/depth controls для честной работы с 3D-моделью через 2D-плоскости.
- Templates: простые георадарные сценарии для студентов и быстрых тестов.

Exit criteria:

- простая модель собирается быстрее через canvas, чем через raw input;
- пользователь понимает выбранный объект, его материал, размеры и координаты без чтения кода;
- случайное действие можно отменить, а скрытые элементы не мешают редактированию.

### Alpha 0.5: gprMax Command Coverage and Import

Цель: расширить покрытие gprMax, не превращая UI в форму на сотни полей.

- Надёжный импорт существующих `.in` файлов с понятным отчётом о поддержанных и неподдержанных командах.
- Guided editor для частых команд: materials, geometry, sources, receivers, waveforms, scans.
- Advanced/raw command editor для редких команд с validation и preview generated input.
- Compatibility notes: что уже поддерживается, что импортируется read-only, что пока требует raw mode.

Exit criteria:

- пользователь может открыть существующий input и понять, что приложение смогло распознать;
- новые модели генерируют gprMax input предсказуемо и воспроизводимо;
- unsupported cases не ломают проект молча, а объясняются.

### Alpha 0.6: Simulation and Results Workflow

Цель: сделать путь “собрал модель -> запустил -> понял результат” цельным.

- Preflight перед запуском: validation, runtime, paths, output, disk space.
- Run lifecycle: start, cancel, retry, rerun from history, clear status.
- Snapshot каждого запуска: input, config, command line, runtime version, logs.
- Results viewer V2: A-scan cursors, B-scan contrast/gain/colormap, screenshots, CSV/PNG export.
- Compare runs: side-by-side и быстрый переход от результата к параметрам запуска.

Exit criteria:

- пользователь запускает расчёт без CLI и понимает, что именно было запущено;
- ошибка запуска объясняется через UI достаточно ясно для следующего действия;
- результаты можно использовать для отчёта, публикации или issue без внешней ручной рутины.

### Beta 0.8: Stability, Documentation, Supportability

Цель: подготовить приложение к широкому тестированию и внешним контрибьюторам.

- CI gates: tests, lint, packaging smoke, installer smoke.
- Sample projects: 2D cylinder B-scan, layered soil, buried utility, student starter.
- User docs: quick start, first model, first run, troubleshooting, reporting bugs.
- Support bundle: app logs, runtime diagnostics, project metadata, redaction of sensitive paths.
- Project format versioning and migrations.

Exit criteria:

- tester can reproduce and report issues with enough context;
- contributor can run tests locally without hidden knowledge;
- project files survive format evolution.

### 1.0 Release Candidate

Цель: стабильная публичная версия для не-программистов.

- Signed installer and clean GitHub release process.
- Stable project format with migration path.
- Documented supported gprMax feature subset.
- Regression suite for core editor, simulation and results workflows.
- Known limitations are explicit, not hidden.

Exit criteria:

- installer-first workflow is reliable enough for broad academic/engineering testing;
- typical GPR model can be created, run and analyzed without leaving the app;
- public GitHub release has assets, checksums, docs, issues workflow and reproducible build notes.

## English

### Vision

`GPRMax Workbench` should become a modern Desktop editor for gprMax aimed at geologists, geophysicists, engineers and students, not programmers. A user should download an installer, install the app, build a model, run a simulation and inspect results without installing Python, Anaconda, repositories or dependencies manually.

Historical reference: [tomsiwek/gprMax-Designer](https://github.com/tomsiwek/gprMax-Designer). It had the right idea: a visual model area, toolbar, draw/move/resize modes, shape list, RMB actions, input import and parse-to-gprMax. Its weakness for broad adoption is also clear: Python/Anaconda/clone/env/run setup, no packaged releases and an outdated UX. Our job is not to copy it, but to surpass it.

### Product Principles

- Installer-first: no manual Python, Anaconda, gprMax or dependency setup.
- Visual-first: most model work happens on the scene, like in strong CAD/GIS/visual editors.
- Precision-first: every visual action has numeric coordinates, dimensions, materials and validation.
- Safe editing: undo/redo, previews, clear hints and protection against accidental actions.
- Scientific traceability: every run keeps input, launch settings, runtime version, logs and outputs.
- Beginner-friendly, expert-capable: students can start, experts still have depth.

### Milestones

- Alpha 0.2.x: scene and materials UX, labels, visibility filters, model-state summary, clearer materials.
- Alpha 0.3: installer-first public testing, bundled runtime diagnostics, clean release assets.
- Alpha 0.4: Scene Editor V1 with undo/redo, multi-select, layer controls, snapping and 3D slice foundation.
- Alpha 0.5: gprMax command coverage, guided import, advanced/raw command mode and compatibility notes.
- Alpha 0.6: simulation and results workflow with preflight, run history, snapshots and A/B-scan analysis.
- Beta 0.8: stability, documentation, sample projects, support bundle, project format migrations.
- 1.0 RC: signed installer, stable format, documented feature subset, regression suite and clean public release process.

### Definition of Success

- A non-programmer can install and use the application without CLI work.
- A typical GPR model can be created, run and analyzed inside the app.
- Errors are actionable and written for users, not just developers.
- The scene editor is understandable at a glance and precise when needed.
- Public releases are clean, reproducible and easy to test.
