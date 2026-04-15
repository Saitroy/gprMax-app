# Alpha 0.2.x UX Sign-Off

> The application is available in two interface languages: Russian and English.

## Русский

### Цель

Alpha `0.2.1` закрывает UX milestone для первого круга тестирования. Мы не доказываем, что приложение уже готово для массового публичного релиза. Мы проверяем, что базовый путь геофизика понятен, не разваливается и даёт конкретную обратную связь.

### Ручной сценарий

1. Установить или запустить текущую сборку приложения.
2. Создать новый проект из стартового экрана.
3. Настроить область моделирования, сетку и time window.
4. Создать или выбрать материалы среды.
5. Добавить геометрический объект.
6. Добавить источник.
7. Добавить приёмник.
8. Проверить сцену: видны ли отдельные элементы, подписи, фильтры слоёв и summary состояния модели.
9. Сохранить проект.
10. Закрыть и снова открыть проект.
11. Проверить `Input Preview`.
12. Если runtime доступен, выполнить короткий запуск и открыть результаты.
13. Записать все странности и неудобства в GitHub Issues.

### Что считается успешным

- Пользователь понимает, где создаются материалы, объекты, источник и приёмник.
- Сцена помогает понять текущее состояние модели, а не выглядит отдельной декоративной картинкой.
- Подписи и фильтры слоёв не мешают работе и помогают в модели с несколькими элементами.
- Проект сохраняется и открывается без потери основных настроек.
- `Input Preview` соответствует ожидаемой модели.
- Любая проблема может быть описана как конкретный issue: шаги, ожидание, фактическое поведение, скриншот.

### Что не блокирует Alpha 0.2.1

- Неполное покрытие всех команд `gprMax`.
- Отсутствие signed installer.
- Отсутствие clean Windows VM sign-off, если сборка идёт только одному доверенному тестеру.
- Ограниченность анализа результатов текущими A-scan и bounded B-scan сценариями.

### Что блокирует переход к Alpha 0.3.0

- Невозможность пройти сценарий “создать модель -> материалы -> источник/приёмник -> сцена -> сохранить”.
- Красный CI на базовых тестах и lint.
- Installer/bundle, который не проходит `smoke_test_bundle.ps1`.
- Отсутствие понятной инструкции для тестера, что установить и куда писать баги.

## English

### Goal

Alpha `0.2.1` closes the first UX milestone. We are not proving that the app is ready for a broad public release yet. We are checking that the basic geophysicist workflow is understandable, does not break, and produces concrete feedback.

### Manual scenario

1. Install or run the current app build.
2. Create a new project from the start screen.
3. Configure domain, grid, and time window.
4. Create or select environment materials.
5. Add a geometry object.
6. Add a source.
7. Add a receiver.
8. Check the scene: separate elements, labels, layer filters, and model-state summary.
9. Save the project.
10. Close and reopen the project.
11. Check `Input Preview`.
12. If runtime is available, run a short simulation and open results.
13. Record confusing behavior and workflow blockers in GitHub Issues.

### Success criteria

- The user understands where materials, objects, source, and receiver are created.
- The scene helps explain the current model state instead of feeling decorative.
- Labels and layer filters help with multi-element models.
- The project saves and reopens without losing core settings.
- `Input Preview` matches the expected model.
- Any issue can be reported with steps, expected behavior, actual behavior, and a screenshot.

### Not blocking Alpha 0.2.1

- Incomplete `gprMax` command coverage.
- No signed installer.
- No clean Windows VM sign-off if the build is only sent to one trusted tester.
- Results analysis limited to current A-scan and bounded B-scan workflows.

### Blocking Alpha 0.3.0

- The “create model -> materials -> source/receiver -> scene -> save” scenario cannot be completed.
- CI is red on base tests or lint.
- Bundle/installer does not pass `smoke_test_bundle.ps1`.
- Tester instructions are unclear about what to install and where to report bugs.
