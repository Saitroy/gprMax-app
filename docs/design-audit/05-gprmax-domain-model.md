# Доменная модель gprMax для дизайнеров

Документ объясняет основные сущности приложения простым языком. Он нужен, чтобы дизайнер мог проектировать интерфейс без глубокого знания Python, CLI и формата входных файлов gprMax.

## 1. Project

**Project** — рабочая папка пользователя. В ней приложение хранит модель, сгенерированные входные файлы, результаты расчётов и вспомогательные данные.

Где в коде:

- `src/gprmax_workbench/domain/models.py`
- `src/gprmax_workbench/application/project_service.py`
- `src/gprmax_workbench/infrastructure/persistence/json_project_store.py`

Текущая структура проекта создаётся через `ProjectService.create_project()`:

- `project.gprwb.json` — основной manifest проекта.
- `generated/` — сгенерированные `.in` файлы.
- `runs/` — папки отдельных запусков симуляции.
- `results/` — результаты.
- `assets/` — пользовательские файлы проекта.

Для дизайнера:

- Проект должен восприниматься как “рабочее пространство”, а не как набор технических файлов.
- Пользователю нужны понятные статусы: новый, сохранён, изменён, готов к запуску, выполняется, завершён, есть ошибки.
- В текущем UI не найден явный guard для несохранённых изменений при создании/открытии другого проекта. Это нужно учесть в будущем дизайне.

## 2. Model

**Model** — описание физической сцены, которую gprMax будет рассчитывать.

Где в коде:

- `ProjectModel`
- `ModelDomain`
- `Project`
- `ModelEditorService`
- `ValidationService`
- `InputPreviewService`

Модель состоит из:

- области расчёта;
- сетки дискретизации;
- временного окна;
- материалов;
- геометрических объектов;
- источников сигнала;
- приёмников;
- импортированной геометрии;
- антенн;
- дополнительных gprMax-команд и Python-блоков.

Для дизайнера:

- Модель должна выглядеть как понятный конструктор физической сцены.
- Обязательные параметры должны быть визуально отделены от продвинутых.
- Пользователь должен всегда понимать, можно ли уже запускать расчёт.

## 3. Domain / Geometry Area

**Domain** — прямоугольная расчётная область, внутри которой находится модель.

Текущие поля:

- размер по X/Y/Z;
- шаг сетки по X/Y/Z;
- временное окно;
- количество трасс сканирования;
- PML cells в доменной модели.

Где в UI:

- `src/gprmax_workbench/ui/widgets/model_editor/general_panel.py`
- часть управления размером также есть в `SceneCanvasPanel`.

Связанные gprMax-команды:

- `#domain`
- `#dx_dy_dz`
- `#time_window`
- `#pml_cells`

Для дизайнера:

- Размеры и шаг сетки должны быть одним из самых понятных блоков.
- Нужны подсказки о единицах измерения.
- Желательно показывать производные параметры: примерное число ячеек, вычислительную нагрузку, предупреждение о слишком мелкой сетке.
- PML сейчас есть в доменной модели и генерации input, но guided UI для boundary/PML почти не выражен. Это missing / recommended.

## 4. Material

**Material** — физические свойства среды или объекта.

Где в коде:

- `MaterialDefinition`
- `MaterialsPanel`
- `ValidationService`

Текущие поля:

- identifier;
- relative permittivity;
- conductivity;
- relative permeability;
- magnetic loss;
- notes;
- tags.

Пресеты:

- air;
- dry_sand;
- wet_soil;
- concrete;
- fresh_water.

Связанная gprMax-команда:

- `#material`

Для дизайнера:

- Материал — доменная сущность для геофизиков, поэтому список материалов должен быть визуально сильнее обычной таблицы настроек.
- Нужны пресеты, цветовые swatches, usage count, понятное предупреждение “материал используется объектами”.
- Удаление материала должно требовать подтверждения, особенно если он используется в геометрии.

## 5. Waveform / Signal

**Waveform** — форма сигнала, которую использует источник.

Где в коде:

- `WaveformDefinition`
- `WaveformsPanel`

Текущие типы:

- `ricker`
- `gaussian`
- `gaussiandot`
- `gaussiandotnorm`

Текущие поля:

- identifier;
- kind;
- amplitude;
- center frequency;
- notes;
- tags.

Связанная gprMax-команда:

- `#waveform`

Для дизайнера:

- Это блок “Сигнал”, а не просто список waveform.
- Нужна мини-визуализация формы сигнала или хотя бы понятный preview для частоты/амплитуды. Сейчас такой preview не найден.
- Частоты лучше показывать в инженерном формате и с подсказками по единицам.

## 6. Source

**Source** — источник электромагнитного сигнала.

Где в коде:

- `SourceDefinition`
- `SourcesPanel`

Текущие типы:

- `hertzian_dipole`
- `magnetic_dipole`
- `voltage_source`

Текущие поля:

- identifier;
- kind;
- axis;
- waveform;
- position X/Y/Z;
- delay;
- resistance для `voltage_source`;
- notes;
- tags.

Связанные gprMax-команды:

- `#hertzian_dipole`
- `#magnetic_dipole`
- `#voltage_source`

Для дизайнера:

- Источник должен быть связан с выбранной waveform визуально и логически.
- Позицию источника желательно редактировать и в форме, и на сцене.
- При неверной позиции нужен inline error рядом с координатами и подсветка на canvas.

## 7. Receiver

**Receiver** — приёмник, который записывает компоненты поля во время расчёта.

Где в коде:

- `ReceiverDefinition`
- `ReceiversPanel`

Текущие поля:

- identifier;
- position X/Y/Z;
- outputs строкой CSV;
- notes;
- tags.

Связанная gprMax-команда:

- `#rx`

Для дизайнера:

- Поле `outputs` сейчас выглядит технически: пользователь вводит строку.
- Recommended: заменить в будущем дизайне на чекбоксы компонентов, например `Ex`, `Ey`, `Ez`, `Hx`, `Hy`, `Hz`, если это соответствует требованиям продукта.
- В Results эти компоненты уже показываются через checklist, поэтому модель взаимодействия должна быть единой.

## 8. Geometry Object

**Geometry object** — объект внутри области расчёта.

Где в коде:

- `GeometryPrimitive`
- `GeometryPanel`
- `SceneCanvasPanel`

Текущие типы:

- box;
- sphere;
- cylinder.

Поля:

- label;
- kind;
- material;
- dielectric smoothing;
- координаты и размеры в зависимости от типа;
- notes;
- tags.

Связанные gprMax-команды:

- `#box`
- `#sphere`
- `#cylinder`

Для дизайнера:

- Это один из главных рабочих сценариев.
- Нужны два режима редактирования: визуальный canvas и точная форма параметров.
- Нужны понятные состояния выбора, drag, resize, snap, validation.
- Текущий canvas функционален, но перегружен: много режимов, toolbars, side panel, inspector и список сущностей на одном экране.

## 9. Geometry Import

**Geometry import** — подключение внешней HDF5-геометрии и файла материалов.

Где в коде:

- `GeometryImportDefinition`
- `LibrariesPanel`
- `InputPreviewService`

Поля:

- identifier;
- geometry file;
- materials file;
- position;
- smoothing;
- notes;
- tags.

Связанная gprMax-команда:

- `#geometry_objects_read`

Для дизайнера:

- Это advanced/semipro сценарий.
- Нужны понятные file states: файл выбран, файл не найден, формат не проверен, файл готов.
- Сейчас есть текстовый preview команды, но нет полноценного preview импортируемой геометрии. Это missing / recommended.

## 10. Antenna

**Antenna** — готовая модель антенны из библиотеки gprMax.

Где в коде:

- `AntennaModelDefinition`
- `LibrariesPanel`
- `src/gprmax_workbench/domain/model_entities.py`

Текущие catalog entries:

- `gprmax_user_libs.gssi_1500`
- `gprmax_user_libs.gssi_400`
- `gprmax_user_libs.mala_1200`

Поля:

- identifier;
- library;
- model;
- module;
- function;
- position;
- base resolution;
- rotate90;
- notes;
- tags.

Для дизайнера:

- Антенны должны ощущаться как библиотека готовых моделей, а не как ручной Python-вызов.
- Технические поля `module` и `function` лучше скрывать в advanced state, оставляя понятный выбор “производитель / модель / ориентация / позиция”.
- Python preview нужен для advanced/debug mode.

## 11. Geometry View

**Geometry view** — запрос на экспорт/просмотр геометрии через gprMax.

Где в коде:

- `GeometryView`
- `InputPreviewService`
- `ValidationService`

Текущее состояние:

- Сущность есть в доменной модели и генерации input.
- Guided UI для управления geometry views в найденных основных панелях не обнаружен.

Для дизайнера:

- Missing / recommended: отдельный блок “Preview/export geometry”.
- Пользователь должен понимать, что geometry-only запуск не является полной симуляцией.

## 12. Advanced Commands

**Advanced commands** — ручные gprMax-команды и Python-блоки.

Где в UI:

- `AdvancedPanel`

Где в коде:

- `advanced_input_overrides`
- `python_blocks`
- `command_registry.py`

Категории шаблонов:

- general;
- materials;
- objects;
- imports;
- sources;
- outputs;
- pml.

Для дизайнера:

- Advanced editor нужен, но не должен быть основным способом работы.
- Raw commands и Python следует визуально маркировать как “для продвинутых”.
- Нужны warnings: ручные команды могут конфликтовать с формами модели.

## 13. Simulation

**Simulation** — запуск gprMax для текущей модели.

Где в UI:

- `src/gprmax_workbench/ui/views/simulation_view.py`

Где в коде:

- `SimulationService`
- `ExecutionConfig`
- `RuntimeService`
- `ResultsService`

Текущие параметры запуска:

- mode: `normal` или `geometry_only`;
- number of model runs;
- geometry fixed;
- write processed;
- restart;
- MPI tasks;
- benchmark;
- MPI no spawn;
- extra args.

В доменной модели есть `use_gpu` и `gpu_device_ids`, но в текущем UI они принудительно выставляются как `False` и пустой список. GPU в интерфейсе запуска не найден. Это needs confirmation для продуктового scope.

Состояния запуска:

- preparing;
- running;
- completed;
- failed;
- cancelled.

Для дизайнера:

- Run Monitor должен явно показывать: что запускается, где gprMax, сколько задач, что уже сделано, где логи, что делать после завершения.
- Сейчас есть статус, readiness, logs и history, но нет явного progress bar/ETA/stepper.
- Ошибки запуска нужно переводить на простой язык, оставляя technical details раскрываемыми.

## 14. Runtime / Environment

**Runtime** — окружение, в котором запускается gprMax.

Где в UI:

- `SettingsView`
- Simulation readiness/status

Где в коде:

- `RuntimeService`
- `RuntimeSettings`
- `RuntimeProbe`
- `SettingsManager`

Что показывается:

- mode;
- install root;
- engine root;
- Python executable;
- app version;
- engine version;
- gprMax version;
- settings/log/cache/temp paths;
- capabilities без GPU capability в Settings UI.

Для дизайнера:

- Это критически важная зона для не-программистов.
- Нужно состояние “gprMax найден / не найден / нужна настройка / проверка выполняется”.
- Нужна кнопка проверки окружения и понятная remediation-инструкция. В текущем Settings UI такой кнопки не найдено.

## 15. Output / Result

**Output** — файлы, созданные gprMax после запуска.

Где в UI:

- `ResultsView`

Где в коде:

- `ResultsService`
- `OutputFile`
- `RunResultSummary`
- `TracePlotWidget`
- `BscanImageWidget`

Текущие представления:

- run list;
- summary selected run;
- output/artifact files;
- A-scan chart;
- B-scan image.

Состояния:

- нет проекта;
- нет запусков;
- запуск без результатов;
- результаты есть;
- ошибка чтения;
- частичные результаты;
- выбран неподдерживаемый файл.

Для дизайнера:

- Results должен быть рабочей областью анализа, не просто списком файлов.
- Missing / recommended: export selected chart/image/data, compare runs, report builder, plot settings.
- Ошибки чтения нужно показывать рядом с конкретным файлом.

## 16. Logs / Errors

**Logs** — технический след работы приложения и gprMax.

Где в UI:

- Simulation Logs section;
- Results summary issues;
- status messages в Project/Settings/Welcome;
- `QMessageBox` для ошибок.

Где в коде:

- `LogEntry`
- `RunArtifacts`
- `SimulationService`
- `RuntimeService`

Для дизайнера:

- Нужно разделить пользовательские сообщения и технические детали.
- Для геофизика главный текст должен отвечать: что случилось, почему это важно, что сделать дальше.
- Технический stdout/stderr нужен в collapsible “Details” или debug mode.

## 17. Validation

**Validation** — проверка корректности проекта, модели и запуска.

Где в коде:

- `ValidationService`
- `ExecutionValidationResult`

Что проверяется:

- обязательные имена и ID;
- положительные размеры, шаг сетки, временное окно;
- PML cells;
- параметры материалов;
- корректность source/waveform/receiver;
- геометрия и материалы;
- существование импортируемых файлов;
- настройки запуска;
- предупреждения по missing source/receiver;
- runtime readiness.

Для дизайнера:

- Validation должна быть inline, grouped и actionable.
- Сейчас сообщения чаще показываются как общие списки/статусы.
- Нужна навигация от ошибки к полю, где её исправить.

