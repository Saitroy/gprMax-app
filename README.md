# GPRMax Workbench

> Приложение доступно на двух языках: русском и английском.
> The application is available in two interface languages: Russian and English.

## Русский

`GPRMax Workbench` — desktop-приложение для работы с проектами `gprMax` без ручного написания input-файлов и без постоянной работы через CLI.

Приложение рассчитано на геофизиков, инженеров, исследователей, преподавателей и студентов, которым нужен понятный рабочий интерфейс: создать проект, настроить модель, запустить расчёт и посмотреть результаты.

> Статус: Alpha `0.2.1` UX-fix milestone. Эта версия закрывает первый цикл улучшений интерфейса редактирования модели. Следующий целевой этап — Alpha `0.3.0` Installer Candidate.

### Что есть в приложении

- `Welcome / Start`: создание нового проекта, открытие существующего, список recent projects, быстрый доступ к примерам и документации.
- `Project`: основная рабочая зона для редактирования модели по понятным секциям.
- `Scene`: визуальная сцена модели с подписями, фильтрами слоёв, summary состояния модели и инспектором выбранного элемента.
- `Materials`: работа с материалами среды в формате, более близком к библиотеке/palette, а не к таблице для программиста.
- `Simulation`: подготовка расчёта, preview/export input, запуск, остановка, live logs и история запусков.
- `Results`: просмотр run artifacts, A-scan, bounded B-scan и выходных файлов.
- `Settings`: язык интерфейса, advanced mode и диагностика runtime.

### Что можно делать в проекте

Во вкладке `Project` модель разбита на понятные рабочие секции:

- `Scene`
- `Domain / Grid / Time Window`
- `Materials`
- `Waveforms`
- `Sources`
- `Receivers`
- `Geometry`
- `Libraries / Imports`
- `Advanced`
- `Input Preview`

Это позволяет редактировать проект по частям, а не работать с одной перегруженной формой.

### Как создать новый проект

1. Откройте приложение.
2. На стартовом экране выберите `New Project`.
3. Укажите папку проекта и имя.
4. После создания приложение откроет рабочую область `Project`.

Новый проект сохраняется как отдельная рабочая папка, в которой приложение будет хранить модель, сгенерированные input-файлы и артефакты запусков.

### Как открыть существующий проект

1. На стартовом экране выберите `Open Project`, либо откройте проект из списка recent.
2. Укажите папку проекта.
3. Приложение загрузит модель, историю запусков и доступные результаты.

### Как редактировать проект

Обычный рабочий сценарий такой:

1. В `Scene` задайте базовую компоновку и посмотрите на модель в рабочем пространстве.
2. Проверьте подписи, фильтры слоёв и состояние модели в `Scene`.
3. В `Domain / Grid / Time Window` настройте расчётную область, дискретизацию и временное окно.
4. В `Materials` создайте и отредактируйте материалы.
5. В `Waveforms`, `Sources` и `Receivers` настройте возбуждение и приём.
6. В `Geometry` добавьте и уточните объекты модели.
7. В `Input Preview` проверьте, какой `gprMax` input будет сгенерирован из текущего проекта.

Проект редактируется секционно, поэтому пользователь видит только ту часть данных, с которой работает в данный момент.

### Как сохранить проект

- После изменений используйте `Save Project`.
- Основное состояние проекта сохраняется в файл `project.gprwb.json` в папке проекта.
- История запусков, логи и сгенерированные файлы хранятся рядом с проектом, а не внутри системных каталогов приложения.

Типичная структура проекта выглядит так:

```text
<project-root>/
  project.gprwb.json
  generated/
  runs/
  results/
  assets/
```

### Как запустить симуляцию

1. Перейдите во вкладку `Simulation`.
2. Проверьте `run readiness` и конфигурацию запуска.
3. При необходимости сначала выполните `Input Preview` или `Export`.
4. Нажмите `Run`.
5. Следите за состоянием запуска и `live logs` прямо в приложении.

После завершения можно открыть папку запуска или папку output-файлов из интерфейса.

### Как смотреть результаты

1. Перейдите во вкладку `Results`.
2. Выберите нужный запуск.
3. Просмотрите найденные output-файлы и метаданные.
4. Откройте A-scan или B-scan preview, если они доступны для выбранного run.

Если результаты отсутствуют, повреждены или ещё не были построены, приложение показывает соответствующее состояние вместо пустого экрана.

### Для кого это приложение

- для тех, кто хочет работать с `gprMax` как с desktop-инструментом, а не как с набором CLI-команд;
- для учебных и исследовательских сценариев;
- для инженерных задач, где важны повторяемые проекты, история запусков и быстрый доступ к результатам.

### Где смотреть дальше

- Фактическое текущее состояние продукта: [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md)
- Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md)
- Alpha 0.2.x UX sign-off: [docs/ALPHA_0_2_UX_SIGNOFF.md](docs/ALPHA_0_2_UX_SIGNOFF.md)
- Release notes: [docs/ALPHA_RELEASE_NOTES.md](docs/ALPHA_RELEASE_NOTES.md)
- Поддержка и bug reports: [SUPPORT.md](SUPPORT.md)
- Техническая документация для разработчиков и release-процесса: [docs/TECHNICAL_GUIDE.md](docs/TECHNICAL_GUIDE.md)

### Как отправлять баг-репорты

Приложение сейчас находится в стадии ALPHA-теста.

Все баг-репорты отправляйте через [GitHub Issues](https://github.com/Saitroy/gprMax-app/issues).

Пожалуйста, не отправляйте баги на личную почту: в GitHub Issues не теряется контекст, видна версия приложения и проще собрать список исправлений.

К issue желательно приложить:

- скриншоты проблемы;
- версию приложения, например `0.2.1`;
- версию Windows;
- краткое описание того, что вы делали перед появлением бага;
- по возможности support bundle, название проекта или run, в котором это произошло.

## English

`GPRMax Workbench` is a desktop application for working with `gprMax` projects without relying on handwritten input files or a CLI-first workflow.

It is designed for geophysicists, engineers, researchers, teachers, and students who want a practical desktop workbench: create a project, edit the model, run a simulation, and inspect the results.

> Status: Alpha `0.2.1` UX-fix milestone. This release closes the first usability pass around model editing. The next target is Alpha `0.3.0` Installer Candidate.

### What the application includes

- `Welcome / Start`: create a new project, open an existing one, reopen recent projects, and access examples and documentation.
- `Project`: the main workspace for model editing through focused sections.
- `Scene`: visual model scene with labels, layer visibility filters, model-state summary, and selected-item inspection.
- `Materials`: clearer material editing shaped more like a material library/palette.
- `Simulation`: run setup, input preview/export, start/stop, live logs, and run history.
- `Results`: run artifacts, A-scan, bounded B-scan, and output browsing.
- `Settings`: language, advanced mode, and runtime diagnostics.

### Typical workflow

1. Create or open a project from `Welcome`.
2. Edit the model in the `Project` workspace section by section.
3. Check scene labels, layer filters, model-state summary, and selected item.
4. Save the project.
5. Move to `Simulation` to validate and run.
6. Open `Results` to inspect outputs and previews.

### Editing and saving projects

The `Project` workspace is split into focused sections:

- `Scene`
- `Domain / Grid / Time Window`
- `Materials`
- `Waveforms`
- `Sources`
- `Receivers`
- `Geometry`
- `Libraries / Imports`
- `Advanced`
- `Input Preview`

Project state is saved into `project.gprwb.json` inside the project folder, with generated files and run artifacts stored alongside the project.

### Learn more

- Current product snapshot: [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md)
- Roadmap: [docs/ROADMAP.md](docs/ROADMAP.md)
- Alpha 0.2.x UX sign-off: [docs/ALPHA_0_2_UX_SIGNOFF.md](docs/ALPHA_0_2_UX_SIGNOFF.md)
- Release notes: [docs/ALPHA_RELEASE_NOTES.md](docs/ALPHA_RELEASE_NOTES.md)
- Support and bug reports: [SUPPORT.md](SUPPORT.md)
- Technical documentation for development and release engineering: [docs/TECHNICAL_GUIDE.md](docs/TECHNICAL_GUIDE.md)

### Bug reports

The application is currently in ALPHA testing.

Please report bugs via [GitHub Issues](https://github.com/Saitroy/gprMax-app/issues) and include:

- screenshots of the problem;
- application version, for example `0.2.1`;
- Windows version;
- a short note about what you were doing right before the bug appeared;
- if possible, a support bundle, project name, or run where it happened.
