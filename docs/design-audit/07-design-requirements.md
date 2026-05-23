# Требования к будущему дизайну

Документ описывает требования к будущему UI. Это не техническое задание на реализацию, а дизайн-рамка для полной переработки интерфейса без потери текущей функциональности.

## 1. Общие принципы

### Desktop first

Основной target — desktop-приложение для Windows/Linux/macOS.

Обязательные размеры для проверки макетов:

- 1366x768;
- 1440x900;
- 1920x1080;
- 2560x1440.

Secondary consideration:

- маленькие ноутбуки;
- tablet-like размеры;
- smartphone view только как потенциальный read-only/secondary сценарий, не основной режим.

### Clean, Google-like minimal UI

Интерфейс должен быть лёгким, спокойным и современным:

- меньше визуального шума;
- ясная иерархия;
- достаточно воздуха;
- нейтральные цвета;
- понятные primary/secondary actions;
- cards только там, где они помогают группировать данные.

### Не перегружать рабочие экраны

Текущий UI функционально богатый, но перегруженный. Новый дизайн должен показывать только то, что нужно для текущего шага, и раскрывать детали по мере необходимости.

Основной паттерн:

- базовые параметры всегда видны;
- advanced параметры свернуты;
- technical details доступны, но не мешают основному сценарию.

### Friendly UX для геофизиков

Пользователь может быть сильным специалистом в геофизике, но не обязан знать:

- Python;
- Git;
- CLI;
- структуру gprMax input file;
- внутренние пути приложения.

Тексты должны отвечать на вопросы:

- что это значит;
- что нужно ввести;
- можно ли уже запускать расчёт;
- что делать, если возникла ошибка.

## 2. Информационная архитектура

Рекомендуемая верхнеуровневая структура:

- Welcome / Home;
- Projects;
- Model Editor;
- Simulation Setup;
- Run Monitor;
- Results;
- Logs / Diagnostics;
- Settings.

Текущий UI имеет:

- Welcome;
- Project;
- Simulation;
- Results;
- Settings как dialog.

Будущий дизайн должен решить, остаётся ли Settings диалогом или становится полноценной зоной.

## 3. Обязательные состояния интерфейса

Для каждой ключевой зоны нужны состояния:

- normal;
- empty;
- loading;
- success;
- error;
- disabled;
- validation error;
- running simulation;
- completed simulation;
- cancelled simulation;
- failed simulation.

Дополнительно:

- unsaved changes;
- read-only/unavailable because no project;
- unavailable because gprMax runtime is not configured;
- partial results;
- missing output file;
- stale run recovered after restart.

## 4. Навигация

### Main navigation

Требования:

- активный экран должен быть очевиден;
- primary screens должны быть доступны в один клик;
- Settings/Diagnostics должны быть заметны, если они блокируют запуск;
- не перегружать sidebar secondary actions.

Рекомендуемый порядок:

1. Home
2. Project
3. Model
4. Simulation
5. Results
6. Diagnostics
7. Settings

### Context navigation

Для Model Editor нужны группы:

- Overview;
- Domain;
- Materials;
- Signal;
- Sources;
- Receivers;
- Geometry;
- Libraries;
- Preview;
- Advanced.

Внутри группы должны быть статусы:

- complete;
- warning;
- error;
- empty;
- advanced.

## 5. Welcome / Home

Назначение:

- первый запуск;
- быстрый вход в работу;
- последние проекты;
- шаблоны/примеры;
- состояние окружения gprMax.

Что должно быть видно сразу:

- Create New Project;
- Open Existing Project;
- Recent Projects;
- Example/Templates;
- Runtime status: ready/not configured.

Что можно спрятать:

- подробные пути окружения;
- technical diagnostics;
- длинные объяснения gprMax.

Нужны компоненты:

- recent project list;
- template cards;
- runtime status banner;
- first-run onboarding hint;
- documentation/help link.

## 6. Projects

Назначение:

- создание, открытие, сохранение и управление проектом.

Обязательные данные:

- name;
- folder;
- manifest status;
- modified/saved state;
- model summary;
- last run/results summary.

Основные actions:

- New;
- Open;
- Save;
- Save As / duplicate, если будет поддержано;
- Open folder;
- Import/export project package, если будет подтверждено;
- Close project.

Требования:

- unsaved changes guard;
- понятное состояние no project;
- предупреждение перед destructive actions;
- явная связь “проект готов/не готов к симуляции”.

## 7. Model Editor

Назначение:

- создать и проверить модель gprMax без ручного написания input-файла.

Что должно быть видно сразу:

- domain summary;
- scene canvas or model overview;
- validation status;
- primary next action: validate / preview / go to simulation.

Основные блоки:

- Domain;
- Materials;
- Geometry;
- Sources;
- Receivers;
- Signal;
- Validation.

Второстепенные блоки:

- notes/tags;
- imported geometry;
- antenna internals;
- raw gprMax commands;
- Python blocks;
- advanced PML settings.

Требования:

- inline validation;
- unit labels;
- clear required fields;
- derived values for grid/workload;
- object selection sync between list/form/canvas;
- confirmation for delete;
- advanced mode for raw commands.

## 8. Simulation Setup

Назначение:

- подготовить запуск и проверить, что всё готово.

Что должно быть видно сразу:

- readiness: ready/not ready;
- selected project/model;
- runtime status;
- run mode;
- number of runs;
- start action.

Advanced:

- MPI tasks;
- restart;
- benchmark;
- extra args;
- GPU/device selection, если продуктово подтверждено.

Требования:

- Start disabled with clear reason when not ready.
- Readiness errors must link back to the place where they can be fixed.
- Preview input should be available, but not dominate the screen.

## 9. Run Monitor

Назначение:

- сопровождать пользователя во время расчёта.

Что должно быть видно сразу:

- status;
- elapsed time;
- current stage;
- progress if available;
- live logs summary;
- Cancel;
- output folder.

После completion:

- open results;
- open output folder;
- export/share logs;
- rerun.

После failure:

- simple explanation;
- likely cause;
- suggested next step;
- technical details collapsible.

## 10. Results

Назначение:

- просмотр и анализ результатов.

Что должно быть видно сразу:

- selected run;
- available outputs;
- primary visualization;
- export action;
- run status.

Основные блоки:

- Run list/history;
- A-scan;
- B-scan;
- artifacts;
- summary;
- issues.

Recommended:

- compare runs;
- export chart/image/data;
- plot settings;
- report/export package;
- annotations/markers if needed by domain users.

Состояния:

- no project;
- no runs;
- run completed but no outputs;
- output unreadable;
- partial results;
- selected file unsupported.

## 11. Logs / Diagnostics

Назначение:

- объяснить ошибки и дать путь к исправлению.

Разделить:

- user-facing status;
- suggested action;
- technical details;
- raw logs.

Требования:

- ошибки простым языком;
- technical logs в collapsible/details;
- copy/export logs;
- filter by run/severity;
- diagnostics for gprMax environment.

## 12. Settings

Назначение:

- настройки приложения, окружения и advanced режима.

Основные блоки:

- language;
- gprMax runtime;
- environment diagnostics;
- advanced mode;
- theme, если будет поддержана;
- performance defaults;
- export defaults;
- reset layout.

Что должно быть видно сразу:

- runtime ready/not ready;
- current mode;
- action to fix.

Advanced:

- exact Python executable;
- engine root;
- cache/temp/log paths;
- raw diagnostics.

## 13. Forms and Inputs

Требования:

- единицы измерения рядом с полями;
- required/optional markers;
- placeholders с примером;
- inline error под полем;
- disabled reason for disabled controls;
- numeric constraints;
- grouped coordinates X/Y/Z;
- инженерное отображение частот и времени.

Особенно важные поля:

- domain size;
- resolution;
- time window;
- material properties;
- source/receiver position;
- waveform frequency;
- run count;
- runtime path.

## 14. Empty States

Обязательные empty states:

- no project open;
- no recent projects;
- no materials beyond defaults;
- no sources;
- no receivers;
- no geometry;
- no runs;
- no results;
- no readable output files;
- no runtime configured.

Каждый empty state должен содержать:

- краткое объяснение;
- primary action;
- secondary help link, если нужно.

## 15. Warning and Error States

Требования:

- warning не должен блокировать, если можно продолжить;
- error должен объяснять, что исправить;
- technical details отдельно;
- одинаковые severity labels across app;
- warnings/errors должны агрегироваться в summary и дублироваться inline.

Примеры:

- no receivers: warning для модели;
- invalid domain size: error;
- missing gprMax: blocking error for simulation;
- output unreadable: result-specific error.

## 16. Advanced Mode

Advanced mode должен:

- открывать raw commands/Python blocks;
- показывать technical paths/logs;
- показывать MPI/GPU/extra args;
- не удалять эти функции из продукта;
- не делать их частью beginner path.

Требования:

- clear “Advanced” label;
- warning before raw command edits;
- explanation that advanced commands can affect generated input.

## 17. Дизайн-система

Нужны базовые компоненты:

- app shell;
- sidebar navigation;
- section navigation;
- action toolbar;
- status banner;
- metric/status tiles;
- form rows;
- coordinate input group;
- validation summary;
- inline field error;
- empty state;
- modal dialog;
- confirmation dialog;
- split panel;
- collapsible advanced panel;
- log viewer;
- chart panel;
- file picker row;
- run status badge.

## 18. Приоритеты редизайна

Высший приоритет:

- unsaved changes and project state;
- Model Editor navigation and density;
- inline validation;
- Simulation readiness and run monitor;
- runtime setup/diagnostics;
- Results export/analysis path.

Средний приоритет:

- Welcome templates/examples;
- PML/boundary guided UI;
- GPU/MPI clarification;
- delete confirmations;
- reset layout;
- documentation/help integration.

