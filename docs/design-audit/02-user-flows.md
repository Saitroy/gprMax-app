# User Flows

## Flow 1: Первый запуск приложения

Текущий путь по коду:

1. `app.run()` строит `ApplicationContext`, вызывает `RuntimeService.refresh()`, создает `QApplication` и `MainWindow`.
2. `MainWindow` показывает Welcome, если нет `current_project`.
3. Welcome показывает hero, New Project, Open Project, Documentation, статус workspace и recent projects.
4. Если recent projects пустые, список содержит disabled item с empty message.
5. Documentation dialog может показать bundled examples, если `examples/summary.json` найден.

Что видит пользователь:

- стартовый экран;
- кнопки создания/открытия проекта;
- статус "нет проекта";
- recent projects или empty state;
- workflow tooltip через info button.

Риски UX:

- примеры не видны на Welcome напрямую, хотя данные examples передаются;
- нет отдельного "quick start/template" блока;
- пользователь не видит checklist "создайте проект -> задайте модель -> запустите".

Что спроектировать:

- Welcome как рабочий hub, а не marketing page;
- прямой блок "Examples / Templates";
- заметный current runtime status;
- friendly first-run guidance без технического перегруза;
- empty state для recent projects с понятным CTA.

## Flow 2: Создание модели с нуля

Текущий путь:

1. Welcome или menu File -> New Project.
2. `NewProjectDialog`: имя проекта, папка, Browse.
3. `ProjectService.create_project()` создает папки `generated`, `runs`, `results`, `assets` и `project.gprwb.json`.
4. `MainWindow.refresh_views()` открывает Project page.
5. Пользователь работает в Project sections:
   - Scene;
   - Domain / Grid / Time Window;
   - Materials;
   - Waveforms;
   - Sources;
   - Receivers;
   - Geometry;
   - Libraries / Imports;
   - Advanced, если включен advanced mode;
   - Input Preview.
6. Изменения идут через `ModelEditorService`, validation обновляется через `ValidationService`.
7. Save Project сохраняет manifest, если нет validation errors.

Что вводит пользователь:

- имя проекта;
- описание проекта;
- title модели;
- размеры domain X/Y/Z;
- discretization X/Y/Z;
- time window;
- материалы;
- waveforms;
- источники;
- приемники;
- геометрию;
- импорты/антенны;
- advanced raw commands при необходимости.

Что должен понять пользователь:

- какие поля обязательны;
- что модель еще не готова к запуску без sources/receivers;
- какие warning можно оставить, а какие error блокируют save/run;
- где он сейчас находится в workflow.

Проблемы текущего UX:

- ошибки не привязаны визуально к полям;
- delete без подтверждения;
- нет пошагового "model completeness";
- PML и geometry views почти не представлены в guided UI;
- Scene и list-detail секции частично дублируют одни и те же сущности.

## Flow 3: Запуск симуляции

Текущий путь:

1. Пользователь открывает Simulation page.
2. `SimulationView` показывает readiness, runtime label, project state, run state.
3. Конфигурация запуска: mode, number of runs, geometry fixed, write processed.
4. Advanced mode добавляет restart, MPI tasks, benchmark, MPI no spawn, extra args.
5. Preview генерирует input через `SimulationService.rebuild_input_preview()`.
6. Export сохраняет `.in` через save file picker.
7. Start вызывает `SimulationService.start_simulation()`.
8. Runtime state обновляется таймером каждые 750 ms.
9. Logs page показывает combined stdout/stderr.
10. После завершения Results refresh и status bar сообщает, что результаты готовы.

Состояния запуска:

- no project;
- not ready;
- ready;
- busy;
- preparing;
- running;
- completed;
- failed;
- cancelled;
- stale run recovered.

Что сейчас не хватает:

- progress bar;
- stage timeline: validate, generate input, start process, running, merge outputs, completed;
- clear primary/secondary action hierarchy;
- GPU UI;
- human-readable recovery для runtime failures.

## Flow 4: Анализ результата

Текущий путь:

1. Пользователь открывает Results.
2. Results refresh читает run summaries из `ResultsService`.
3. Пользователь выбирает run.
4. Summary panel показывает metadata.
5. A-scan tab: выбрать output, receiver, компоненты.
6. B-scan tab: выбрать output, receiver, component.
7. Можно открыть output folder или selected file.

Состояния:

- нет открытого проекта;
- нет результатов;
- run выбран, но output files нет;
- output file unreadable;
- receiver/component отсутствует;
- B-scan невозможен, если нет merged output или минимум двух individual traces;
- результат загружен.

Что не хватает:

- экспорт графика/изображения;
- compare runs;
- сохранение отчета;
- управление масштабом, цветовой шкалой, единицами и диапазоном;
- loading state при чтении больших файлов.

## Flow 5: Ошибка в параметрах

Текущий путь:

1. Пользователь вводит невалидное значение или оставляет обязательную связь пустой.
2. `ModelEditorService` обновляет in-memory project.
3. `validate_project()` собирает `ValidationIssue` с path и severity.
4. Секция показывает текстовый status label.
5. Project summary показывает счетчик errors/warnings.
6. Save или Start могут показать `QMessageBox.warning` со списком ошибок.

Примеры ошибок:

- project name empty;
- domain/resolution/time window <= 0;
- duplicate identifiers;
- geometry without material;
- source without waveform;
- coordinates outside domain;
- missing geometry import files;
- runtime unhealthy.

Как должен работать будущий UI:

- inline подсветка поля;
- короткое объяснение простым языком;
- technical path в раскрываемом блоке;
- action hint, например "создайте материал или выберите free_space";
- переход к проблемной секции;
- status summary не заменяет field-level errors.

## Flow 6: Проблема с gprMax core/runtime

Текущий путь:

1. `RuntimeService.refresh()` выбирает bundled или external runtime.
2. `SettingsView` показывает runtime summary, capabilities, diagnostics.
3. `SimulationService.assess_run_readiness()` проверяет runtime probe, diagnostics, capabilities, writable paths, disk space.
4. Если runtime не готов, Start заблокирован или показывает warning.

Возможные причины:

- gprMax runtime unhealthy;
- external Python path неверный;
- pycuda/mpi4py недоступны;
- project path not writable;
- low disk space;
- subprocess start failed.

Проблемы текущего UX:

- Diagnostics находится в Settings dialog, не рядом с Run readiness;
- runtime executable вводится вручную, без Browse;
- GPU capability не выводится в Settings capabilities;
- сообщения могут быть техническими для геофизика без Python/CLI опыта.

Дизайнерское решение:

- отдельная карточка "Environment check";
- статусы "ready / needs setup / failed";
- кнопки "Choose Python", "Use bundled runtime", "Copy diagnostics";
- friendly explanation и collapsible details.

