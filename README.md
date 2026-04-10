# GPRMax Workbench

## Русский

`GPRMax Workbench` — desktop-приложение для работы с проектами `gprMax` без ручного написания input-файлов и без постоянной работы через CLI.

Приложение рассчитано на геофизиков, инженеров, исследователей, преподавателей и студентов, которым нужен понятный рабочий интерфейс: создать проект, настроить модель, запустить расчёт и посмотреть результаты.

> Статус: приложение находится в активной разработке и сейчас проходит ALPHA-тест. Уже сейчас оно пригодно для раннего тестирования и прикладной работы, но отдельные функции и интерфейсы ещё продолжают стабилизироваться.

### Что есть в приложении

- `Welcome / Start`: создание нового проекта, открытие существующего, список recent projects, быстрый доступ к примерам и документации.
- `Project`: основная рабочая зона для редактирования модели.
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
2. В `Domain / Grid / Time Window` настройте расчётную область, дискретизацию и временное окно.
3. В `Materials` создайте и отредактируйте материалы.
4. В `Waveforms`, `Sources` и `Receivers` настройте возбуждение и приём.
5. В `Geometry` добавьте и уточните объекты модели.
6. В `Input Preview` проверьте, какой `gprMax` input будет сгенерирован из текущего проекта.

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
- Поддержка и bug reports: [SUPPORT.md](SUPPORT.md)
- Техническая документация для разработчиков и release-процесса: [docs/TECHNICAL_GUIDE.md](docs/TECHNICAL_GUIDE.md)

### Как отправлять баг-репорты

Приложение сейчас находится в стадии ALPHA-теста.

Все баг-репорты отправляйте через [GitHub Issues](https://github.com/Saitroy/gprMax-app/issues).

К issue желательно приложить:

- скриншоты проблемы;
- краткое описание того, что вы делали перед появлением бага;
- по возможности название проекта или run, в котором это произошло.

## English

`GPRMax Workbench` is a desktop application for working with `gprMax` projects without relying on handwritten input files or a CLI-first workflow.

It is designed for geophysicists, engineers, researchers, teachers, and students who want a practical desktop workbench: create a project, edit the model, run a simulation, and inspect the results.

> Status: the application is in active development and currently in ALPHA testing.

### What the application includes

- `Welcome / Start`: create a new project, open an existing one, reopen recent projects, and access examples and documentation.
- `Project`: the main workspace for model editing.
- `Simulation`: run setup, input preview/export, start/stop, live logs, and run history.
- `Results`: run artifacts, A-scan, bounded B-scan, and output browsing.
- `Settings`: language, advanced mode, and runtime diagnostics.

### Typical workflow

1. Create or open a project from `Welcome`.
2. Edit the model in the `Project` workspace section by section.
3. Save the project.
4. Move to `Simulation` to validate and run.
5. Open `Results` to inspect outputs and previews.

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
- Support and bug reports: [SUPPORT.md](SUPPORT.md)
- Technical documentation for development and release engineering: [docs/TECHNICAL_GUIDE.md](docs/TECHNICAL_GUIDE.md)

### Bug reports

The application is currently in ALPHA testing.

Please report bugs via [GitHub Issues](https://github.com/Saitroy/gprMax-app/issues) and include:

- screenshots of the problem;
- a short note about what you were doing right before the bug appeared;
- if possible, the project or run where it happened.
