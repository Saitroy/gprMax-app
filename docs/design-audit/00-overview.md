# Design Audit: GPRMax Workbench

Дата аудита: 2026-05-23.

Цель документации - дать фронт-дизайнерам и UX-дизайнерам полную карту текущего PySide6-интерфейса, чтобы они могли проектировать следующий дизайн без глубокого погружения в код.

## На чем основан аудит

Проверены UI, доменные модели и сервисные связи в коде:

- `src/gprmax_workbench/app.py` - сборка `ApplicationContext`, сервисы, runtime, запуск `MainWindow`.
- `src/gprmax_workbench/ui/main_window.py` - app shell, меню, глобальная навигация, роутинг экранов, project/simulation/results orchestration.
- `src/gprmax_workbench/ui/views/*.py` - Welcome, Project, Simulation, Results, Settings.
- `src/gprmax_workbench/ui/widgets/model_editor/*.py` - все секции редактора модели.
- `src/gprmax_workbench/ui/widgets/results/*.py` - A-scan, B-scan, summary.
- `src/gprmax_workbench/ui/dialogs/*.py` - New Project, Settings, Documentation.
- `src/gprmax_workbench/domain/*.py` и `src/gprmax_workbench/application/services/*.py` - данные, валидация, симуляции, результаты, настройки.

В интерфейсе нет `.ui` файлов Qt Designer. Все элементы создаются программно в Python.

## Продукт и аудитория

`GPRMax Workbench` - desktop-приложение над `gprMax` для геофизиков, инженеров, исследователей, преподавателей и студентов, которым нужен понятный UI вместо ручного написания input-файлов и работы через CLI.

Основной пользователь не обязан знать Python, Git, терминал или внутреннюю структуру `gprMax`. Интерфейс должен помогать:

- создать или открыть проект;
- описать расчетную область, материалы, геометрию, источники и приемники;
- проверить модель;
- запустить расчет;
- увидеть статус, логи и ошибки;
- открыть A-scan/B-scan и файлы результатов;
- экспортировать input или результаты.

## Текущая структура интерфейса

Главное окно реализовано как desktop shell:

- левый sidebar с навигацией по страницам;
- `QStackedWidget` для страниц;
- `QScrollArea` вокруг каждой страницы;
- меню `File`, `Settings`, `Help`;
- status bar;
- отдельные модальные и немодальные диалоги.

Текущие страницы в главной навигации:

1. Welcome.
2. Project.
3. Simulation.
4. Results.

Settings реализован как отдельный dialog, а не как страница главной навигации, хотя `SettingsView` существует как полноценный виджет.

## Главные UX-проблемы

1. **Нет защиты от потери несохраненных изменений.** `New Project` и `Open Project` сразу заменяют текущий проект, явного prompt "save/discard/cancel" в `MainWindow` не найдено.
2. **Settings не является полноценной частью навигации.** Пользователь открывает настройки через меню, а не видит их рядом с Project/Simulation/Results.
3. **Welcome не показывает примеры напрямую.** `WelcomeView.set_example_projects()` сохраняет список, но кнопки примеров реально выводятся в `DocumentationDialog`.
4. **Validation mostly text-based.** Ошибки собираются в статусных текстах секций и message boxes, но почти не подсвечиваются inline у конкретных полей.
5. **Project/Scene перегружены.** В Project есть 10 секций, а Scene совмещает canvas, toolbar, domain controls, palette, inspector, entity list, legend, model summary и validation.
6. **Simulation не показывает настоящий progress bar.** Есть статус, readiness, run history и live logs, но нет процента, этапов, ETA или структурированного прогресса.
7. **GPU предусмотрен в доменной модели, но не выведен в UI.** `SimulationRunConfig.use_gpu` есть, но `SimulationView.current_configuration()` всегда задает `use_gpu=False`.
8. **PML и geometry views есть в модели/генераторе, но почти не имеют guided UI.** Они доступны через advanced templates/raw commands, а не как понятные формы.
9. **Удаление сущностей происходит без подтверждения.** Delete в Material/Waveform/Source/Receiver/Geometry/Libraries/Scene сразу меняет модель.
10. **Экспорт результатов ограничен.** Results умеет открыть output directory или selected file, но не имеет отдельного UX для export/report/compare.

## Что уже хорошо реализовано

- Есть рабочий end-to-end путь: создать проект, настроить модель, preview input, run, посмотреть результаты.
- UI разделен по workspace: Welcome, Project, Simulation, Results.
- Project не является одной огромной формой: модель разбита на секции.
- Scene уже дает визуальную сборку модели: XY/XZ/YZ, drag/drop, zoom, rulers, layer filters, labels, inspector, nudge, undo/redo.
- Simulation учитывает readiness, runtime diagnostics, run history, cancel/retry и live logs.
- Results поддерживает A-scan и B-scan, metadata summary, artifact list.
- Настройки уже сохраняют язык, advanced mode, runtime path и UI state.

## Что важно дизайнерам

Дизайнерам нужно проектировать не только красивые экраны, а систему состояний:

- нет проекта;
- проект создан, но пуст;
- проект изменен и не сохранен;
- модель невалидна;
- модель валидна, но gprMax runtime не готов;
- расчет выполняется;
- расчет завершен;
- расчет отменен или упал;
- результатов нет;
- результаты есть, но output-файл не читается;
- advanced mode выключен или включен.

Следующий дизайн должен быть desktop-first, легкий, современный, не перегруженный, но не скрывать профессиональные возможности `gprMax`.

## Границы уверенности

Все выводы основаны на текущем коде проекта. Если часть логики подразумевается, но UI не найден, она помечается как `missing / recommended` или `needs confirmation`.

