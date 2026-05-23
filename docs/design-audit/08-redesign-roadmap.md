# Roadmap редизайна

Roadmap описывает поэтапный путь к полноценному дизайну приложения. Он не предполагает немедленной реализации и не требует удаления текущих функций.

## Stage 1: Стабилизация структуры интерфейса

Цель:

- Зафиксировать будущую информационную архитектуру.
- Решить, какие зоны являются основными экранами, а какие остаются диалогами/панелями.

Ключевые решения:

- Settings: отдельная страница или dialog.
- Projects: отдельный project browser или расширенный Welcome.
- Model Editor: единый экран с секциями или wizard-like flow.
- Simulation: разделить Setup и Run Monitor или оставить в одном экране с состояниями.
- Logs/Diagnostics: отдельная зона или часть Simulation/Settings.

Дизайн-результаты:

- sitemap;
- navigation model;
- screen inventory;
- state map;
- rules for advanced mode.

Проверка:

- Пользователь на первом запуске понимает, что делать.
- Пользователь с открытым проектом понимает следующий шаг.
- Пользователь с ошибкой окружения видит путь исправления.

## Stage 2: Дизайн-система

Цель:

- Создать единый язык компонентов для всего приложения.

Компоненты:

- app shell;
- sidebar;
- section nav;
- toolbar;
- status banner;
- primary/secondary/destructive buttons;
- form fields;
- coordinate input group;
- validation summary;
- inline error;
- empty state;
- modal;
- confirmation dialog;
- collapsible advanced panel;
- log viewer;
- chart container;
- run status badge.

Правила:

- cards использовать умеренно;
- primary action один на рабочую зону;
- advanced параметры не смешивать с базовыми;
- technical details раскрываются по требованию;
- все состояния описаны заранее.

Проверка:

- Один и тот же тип ошибки выглядит одинаково на Project, Simulation и Results.
- Disabled controls объясняют, почему они недоступны.
- Формы читаются на 1366x768 без критичного переполнения.

## Stage 3: Редизайн Welcome / Projects

Цель:

- Сделать быстрый и понятный вход в приложение.

Основные блоки:

- Create new project;
- Open existing project;
- Recent projects;
- Example/template projects;
- gprMax environment status;
- short help/documentation.

Состояния:

- first launch;
- no recent projects;
- recent project missing;
- runtime ready;
- runtime not configured;
- project creation error.

Дизайн-результаты:

- Welcome screen mockups;
- New Project dialog;
- project card/list pattern;
- onboarding hints;
- runtime warning banner.

Особое внимание:

- Не перегружать Welcome техническими путями.
- Примеры должны быть доступны сразу, а не только через Documentation dialog.
- Unsaved changes guard должен быть частью project lifecycle.

## Stage 4: Редизайн Model Editor

Цель:

- Превратить текущий плотный набор панелей в понятный конструктор модели.

Основные блоки:

- model overview/status;
- domain and mesh;
- materials;
- geometry;
- signal;
- sources;
- receivers;
- libraries/imports;
- validation;
- input preview;
- advanced commands.

Что видно сразу:

- canvas or model overview;
- readiness/validation;
- domain summary;
- primary action: validate/preview/go to simulation.

Что скрывать:

- raw commands;
- Python blocks;
- imported geometry internals;
- antenna module/function;
- advanced PML;
- notes/tags, если они не нужны в основном сценарии.

Дизайн-результаты:

- Model Editor IA;
- Scene canvas layout;
- object inspector pattern;
- entity list pattern;
- validation pattern;
- section navigation;
- advanced drawer/panel.

Особое внимание:

- Синхронизация canvas, списка и формы.
- Inline validation с переходом к полю.
- Удаление сущностей с подтверждением.
- Отдельное решение для PML/boundary.

## Stage 5: Редизайн Simulation

Цель:

- Сделать запуск безопасным и понятным.

Рекомендуемое разделение:

- Simulation Setup;
- Run Monitor;
- Run History.

Simulation Setup:

- readiness status;
- runtime status;
- run mode;
- number of runs;
- geometry fixed;
- write processed;
- preview input;
- Start.

Advanced:

- restart;
- MPI;
- benchmark;
- extra args;
- GPU/devices, если подтверждено.

Run Monitor:

- current run status;
- progress/stage;
- elapsed time;
- live user-facing status;
- logs;
- cancel;
- output folder.

Дизайн-результаты:

- setup screen;
- running state;
- completed state;
- failed state;
- cancelled state;
- log details pattern.

Особое внимание:

- Start disabled state должен объяснять конкретную причину.
- Ошибки gprMax должны иметь простой текст и раскрываемые technical details.
- После success нужен явный переход к Results.

## Stage 6: Редизайн Results

Цель:

- Сделать Results полноценной зоной анализа, а не только просмотром output files.

Основные блоки:

- run selector/history;
- output selector;
- A-scan;
- B-scan;
- summary;
- artifacts;
- issues;
- export.

Recommended features:

- compare runs;
- export data;
- export chart/image;
- export report;
- plot settings;
- annotations/markers, если нужно геофизикам.

Состояния:

- no runs;
- no outputs;
- reading/loading;
- output error;
- partial outputs;
- completed with results.

Дизайн-результаты:

- Results screen IA;
- visualization toolbar;
- export menu;
- empty/error states;
- comparison pattern.

Особое внимание:

- Primary visualization должна быть в фокусе.
- Файлы и artifacts важны, но не должны вытеснять анализ.
- Ошибки чтения показывать рядом с конкретным файлом.

## Stage 7: Logs / Diagnostics / Settings

Цель:

- Снизить барьер для пользователей без Python/CLI опыта.

Settings:

- language;
- runtime;
- advanced mode;
- theme, если будет;
- performance defaults;
- export defaults;
- reset layout.

Diagnostics:

- gprMax found/not found;
- Python executable;
- version check;
- path check;
- dependency check;
- disk/path permissions;
- copy/export diagnostics.

Logs:

- user-facing event timeline;
- severity filters;
- run logs;
- technical details;
- export logs.

Дизайн-результаты:

- Settings screen/dialog;
- environment setup flow;
- diagnostics result view;
- log viewer;
- error detail pattern.

Особое внимание:

- Не показывать raw paths как основной текст ошибки.
- Давать actionable next step.
- Technical details должны быть доступны для поддержки и advanced users.

## Stage 8: Адаптивность и polish

Цель:

- Проверить и довести интерфейс для основных desktop-размеров.

Обязательные viewport checks:

- 1366x768;
- 1440x900;
- 1920x1080;
- 2560x1440.

Проверить:

- помещается ли main navigation;
- не ломается ли Project section toolbar;
- не переполняется ли Scene side panel;
- доступны ли primary actions без лишнего scroll;
- таблицы и списки имеют controlled scroll;
- splitters имеют разумные минимальные размеры;
- текст не обрезается;
- dialogs помещаются на маленьких ноутбуках.

Polish:

- focus states;
- keyboard navigation;
- consistent spacing;
- consistent severity colors;
- tooltips for technical terms;
- empty states;
- loading states;
- disabled reasons;
- reset layout.

Дизайн-результаты:

- responsive rules;
- min/max panel sizes;
- collapsed panel states;
- final design QA checklist.

## Рекомендуемый порядок приоритетов

1. Project lifecycle and unsaved changes.
2. Model Editor information architecture.
3. Inline validation and error navigation.
4. Runtime setup and Simulation readiness.
5. Run Monitor states.
6. Results analysis/export.
7. Welcome templates/onboarding.
8. Settings/Diagnostics polish.
9. Advanced mode cleanup.
10. Responsive QA.

## Что нельзя потерять при редизайне

- Все текущие сущности модели: domain, materials, waveforms, sources, receivers, geometry, imports, antennas.
- Advanced raw commands and Python blocks.
- Input preview/export.
- Simulation config, включая advanced MPI/restart/extra args.
- Run logs/history.
- A-scan and B-scan.
- Runtime diagnostics.
- Recent projects.
- Documentation/examples access.

## Главный критерий успеха

Дизайн успешен, если геофизик без опыта программирования может:

1. создать проект;
2. задать модель;
3. понять, корректна ли она;
4. запустить расчёт;
5. увидеть статус выполнения;
6. открыть и экспортировать результаты;
7. понять и исправить типичные ошибки окружения или параметров.

