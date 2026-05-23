# UX-проблемы и риски текущего интерфейса

Документ фиксирует проблемы, найденные по коду и текущей структуре UI. Это не список задач на немедленную разработку, а входные данные для будущего дизайна.

## Критичные проблемы

### P0. Нет явного guard для несохранённых изменений

Где видно:

- `src/gprmax_workbench/ui/main_window.py`
- действия New Project / Open Project / close window

Проблема:

- В коде не найден явный диалог “сохранить изменения?” перед созданием нового проекта, открытием другого проекта или закрытием окна.
- Состояние `project.modified` существует и отображается, но пользовательский guard не обнаружен.

Почему важно:

- Пользователь может потерять изменения модели.
- Для desktop-приложения с проектами это базовое ожидание.

Что нужно дизайнерам:

- Спроектировать состояния changed/saved.
- Спроектировать confirm dialog: Save / Do not save / Cancel.
- Учесть запуск симуляции: нельзя тихо заменить проект во время active run.

### P0. Модельный редактор перегружен

Где видно:

- `ProjectView`
- `SceneCanvasPanel`
- панели General/Materials/Waveforms/Sources/Receivers/Geometry/Libraries/Advanced/Preview

Проблема:

- Пользователь видит много сущностей, режимов и технических параметров.
- Scene содержит canvas, toolbar, layers, history, snap/grid/domain controls, palette, inspector, entity list, validation.
- Project дополнительно имеет toolbar sections и hidden context navigation.

Почему важно:

- Новичку трудно понять, с чего начинать.
- Геофизик может быть уверен в предметной области, но не обязан понимать структуру gprMax input-файла.

Что нужно дизайнерам:

- Разделить “быстрый путь” и advanced controls.
- Ввести progressive disclosure.
- Сформировать понятную иерархию: область расчёта, материалы, объекты, источники/приёмники, проверка.

### P0. Ошибки и validation недостаточно связаны с конкретными полями

Где видно:

- `ValidationService`
- `ProjectView._update_status`
- `SceneCanvasPanel` validation card
- Simulation readiness messages

Проблема:

- Validation есть, но UI в основном показывает summary/status.
- Не найден единый паттерн inline error рядом с конкретным полем и переходом к проблемному месту.

Почему важно:

- Пользователь видит “модель не готова”, но может не понимать, где именно исправлять.

Что нужно дизайнерам:

- Inline validation для обязательных параметров.
- Error summary с кликабельными переходами к секциям/полям.
- Простые тексты ошибок + technical details в раскрытии.

## Высокий приоритет

### P1. Welcome не раскрывает быстрый старт и примеры

Где видно:

- `WelcomeView.set_example_projects()`
- `DocumentationDialog`

Проблема:

- Welcome принимает список example projects, но в найденном UI не рендерит их как отдельные карточки/кнопки.
- Примеры доступны через Documentation dialog, а не как первичный onboarding.

Почему важно:

- Для первого запуска пользователю нужен быстрый путь: создать пустой проект или открыть готовый пример.

Что нужно дизайнерам:

- Добавить first-run path: New project, Open project, Open example/template.
- Показать последние проекты и шаблоны прямо на Welcome.
- Коротко объяснить назначение приложения.

### P1. Settings не является полноценной зоной навигации

Где видно:

- `MainWindow._build_page_specs()` содержит Welcome/Project/Simulation/Results.
- Settings открывается через `SettingsDialog`.

Проблема:

- Runtime/environment критичны для запуска gprMax, но Settings скрыты в меню.
- Для пользователя без Python/CLI опыта проблемы окружения являются основным blocker.

Что нужно дизайнерам:

- Решить, Settings остаются диалогом или становятся отдельной страницей.
- В любом случае нужна заметная диагностика окружения.
- На Welcome/Simulation должен быть понятный CTA “Настроить gprMax”, если readiness failed.

### P1. Нет полноценного Run Monitor с прогрессом

Где видно:

- `SimulationView`

Проблема:

- Есть статус, readiness, logs, history, но нет явного progress bar, ETA, stepper или понятной стадии.
- Пользователь видит technical logs, но не видит простую картину выполнения.

Почему важно:

- Симуляции могут длиться долго.
- Пользователь должен понимать: расчёт идёт, завис, завершился, отменяется или упал.

Что нужно дизайнерам:

- Спроектировать Run Monitor: current step, elapsed time, output folder, live log, cancel, after-run actions.
- Состояния: preparing, running, cancelling, completed, failed, cancelled.

### P1. Runtime diagnostics недостаточно actionable

Где видно:

- `SettingsView`
- `RuntimeService`
- Simulation readiness

Проблема:

- Settings показывает много путей и runtime summary.
- Не найден browse для external executable.
- Не найден явный “Check environment” action в Settings UI.
- GPU capability исключается из Settings summary.

Что нужно дизайнерам:

- Сценарий “gprMax не найден” должен быть отдельным UX flow.
- Нужны понятные инструкции без Git/Python терминологии как основной линии.
- Technical paths оставить в advanced/details.

### P1. Results пока больше похож на просмотр файлов, чем на анализ

Где видно:

- `ResultsView`
- `TracePlotWidget`
- `BscanImageWidget`

Проблема:

- Есть A-scan и B-scan, run summary и artifacts.
- Не найдено: export chart/image/data, compare runs, plot settings, report, annotations.

Почему важно:

- Для геофизиков Results — ключевая ценность после расчёта.

Что нужно дизайнерам:

- Проектировать Results как рабочую аналитическую область.
- Выделить primary actions: view, compare, export.
- Empty/error states должны объяснять, почему результатов нет.

### P1. Навигация между Project sections может быть неочевидной

Где видно:

- `ProjectView`
- `_section_toolbar`
- `_nav_card.setVisible(False)`

Проблема:

- В коде есть context navigation list, но она скрыта.
- Основная навигация по секциям реализована набором checkable buttons в FlowLayout.

Почему важно:

- При большом количестве секций пользователь может потеряться.
- На маленьких ноутбуках toolbar может переноситься и занимать много места.

Что нужно дизайнерам:

- Выбрать устойчивую модель навигации: sidebar, tabs, stepper или grouped navigation.
- Показывать активную секцию и readiness каждой секции.

## Средний приоритет

### P2. Дублирование preview

Где видно:

- `ProjectView` section Preview
- `SimulationView` section Preview

Проблема:

- Пользователь может не понимать разницу между preview в Project и preview в Simulation.

Что нужно дизайнерам:

- Развести смыслы:
  - Model input preview как часть проверки модели;
  - Run preview как “что будет запущено”.
- Или объединить preview в единый паттерн.

### P2. Удаление сущностей требует более безопасного паттерна

Где видно:

- `MaterialsPanel`
- `WaveformsPanel`
- `SourcesPanel`
- `ReceiversPanel`
- `GeometryPanel`
- `LibrariesPanel`
- `SceneCanvasPanel` context menu

Проблема:

- В панелях есть Delete actions, но по коду не видно единого confirm-паттерна.

Почему важно:

- Удаление материала/источника/геометрии может сломать модель.

Что нужно дизайнерам:

- Confirmation для destructive actions.
- Предупреждение о зависимостях: материал используется объектами, waveform используется source.
- Undo pattern, если он продуктово допустим.

### P2. PML и boundary conditions почти не представлены как guided UI

Где видно:

- `ModelDomain.pml_cells`
- `InputPreviewService`
- `command_registry.py`

Проблема:

- PML есть в модели/generator/templates, но не выглядит как отдельная понятная настройка в UI.

Что нужно дизайнерам:

- Добавить в будущую структуру раздел Boundary/PML.
- Скрывать продвинутые параметры, но показывать базовое состояние boundary setup.

### P2. GPU/MPI scope неясен

Где видно:

- `ExecutionConfig` поддерживает `use_gpu`, `gpu_device_ids`.
- `SimulationView._current_config()` выставляет `use_gpu=False`.
- Settings capabilities скрывает GPU item.

Проблема:

- В архитектуре GPU есть, но UI не даёт его включить.

Что нужно дизайнерам:

- Needs confirmation: будет ли GPU официальной функцией.
- Если да, нужны controls для CPU/GPU, devices, compatibility warnings.
- Если нет, лучше не показывать GPU в пользовательских сценариях.

### P2. Results loading/error states выражены слабо

Где видно:

- `ResultsView.refresh()`
- run list / summary / chart placeholders

Проблема:

- Есть empty-like сообщения, но не видно отдельной визуальной системы loading/error/partial results.

Что нужно дизайнерам:

- Empty state для no project / no runs / no outputs.
- Error state для unreadable output.
- Partial state для run completed with missing artifacts.

### P2. Размеры и layout могут быть проблемой на маленьких экранах

Где видно:

- `MainWindow` minimum size 920x680, initial 1440x920.
- Every page wrapped in `QScrollArea`.
- Project/Simulation/Results используют splitters и dense cards.

Проблема:

- На 1366x768 часть интерфейса неизбежно будет требовать scroll.
- Scene side panel + canvas + toolbar могут быть тесными.

Что нужно дизайнерам:

- Desktop-first layouts для 1366x768 и 1440x900 как обязательные.
- Collapsible side panels.
- Sticky primary actions.
- Таблицы/формы только внутри контролируемых scroll areas.

### P2. Технические сообщения могут попадать в пользовательский слой

Где видно:

- Runtime summary paths.
- Simulation logs.
- Preview generated input.
- Advanced commands/Python blocks.

Проблема:

- Пользователь может видеть Python/gprMax/internal paths без контекста.

Что нужно дизайнерам:

- Разделить:
  - user-facing problem;
  - suggested action;
  - technical details.
- Для advanced/debug mode оставить raw logs and paths.

## Низкий и средний приоритет polish

### P3. Тема выглядит card-heavy

Где видно:

- `src/gprmax_workbench/ui/theme.py`
- многие панели используют `QFrame#Card`

Проблема:

- Карточки полезны, но при большом количестве блоков могут визуально перегружать рабочие экраны.

Что нужно дизайнерам:

- Сохранить лёгкий clean style.
- Использовать cards только для отдельных логических блоков, не вкладывать визуальную тяжесть в каждую форму.

### P3. Нет явного reset layout

Где видно:

- MainWindow сохраняет splitter/page state через settings.

Проблема:

- Если layout “сломался” или стал неудобным, пользователь не видит очевидного reset.

Что нужно дизайнерам:

- Recommended: action “Reset layout” в View/Settings.

### P3. Smartphone/tablet не поддерживаются как основной target

Где видно:

- Desktop Qt app, minimum 920x680.

Проблема:

- Smartphone view может быть только secondary consideration.

Что нужно дизайнерам:

- Не проектировать mobile как основной режим.
- Для tablet/small laptop нужны adaptive/collapsible panels, а не mobile-first навигация.

## Missing / Recommended зоны

Эти элементы не найдены как полноценные пользовательские зоны, но логически нужны продукту:

- полноценная страница Projects/Project Browser;
- шаблоны моделей на Welcome;
- импорт/экспорт проекта как пакета;
- wizard первого проекта;
- guided PML/boundary conditions;
- geometry view/export UI;
- signal preview;
- inline field validation;
- compare results;
- export plot/image/data/report;
- environment check wizard;
- advanced/debug toggle для technical logs;
- reset layout;
- confirmation для destructive actions;
- user-friendly error catalog.

## Needs Confirmation

Нужно уточнить у владельцев продукта:

- Будет ли GPU официально доступен пользователю.
- Какие gprMax-команды должны иметь guided UI, а какие останутся advanced raw commands.
- Нужен ли полноценный Project Browser или достаточно Welcome recent projects.
- Какие форматы экспорта результатов обязательны.
- Нужно ли создавать отчёты прямо из приложения.
- Какие шаблоны/примеры должны быть доступны на первом запуске.
- Должны ли Settings быть отдельной страницей навигации.

