# UI Workstream

## Русский

Этот документ фиксирует поэтапное развитие интерфейса `GPRMax Workbench` после Stage 1-6 foundation.

### Цель

Сначала сделать убедимую, тестопригодную рабочую оболочку для геофизиков и инженеров, а уже потом поэтапно вводить более сложные возможности редактора и advanced tooling.

### UI Phase 1

Статус: реализовано в текущей итерации.

Что включено:

- более человеко-ориентированная shell-оболочка с постоянным контекстом проекта;
- dashboard-подход для стартового экрана;
- встроенные example-проекты как часть onboarding-пути;
- summary tiles для проекта и симуляции;
- более адаптивные splitters и reflow для ключевых экранов;
- более цельная визуальная система с рабочими карточками и мягкой корпоративной палитрой.

### UI Phase 2

Следующий шаг после интерфейсного smoke-тестирования:

- пересборка Model Editor вокруг guided sections и сценариев пользователя;
- отдельное разделение basic / advanced flows внутри simulation configuration;
- более сильные empty / loading / error / success states на всех экранах;
- визуальное усиление Results Viewer, включая более читаемый B-scan layout;
- ввод entity-aware inline help и предупреждений в местах, где пользователи реально ошибаются.

### Feature Phase 3

Функции, сознательно отложенные после shell/UX-итерации:

- 2D/3D canvas editing;
- drag-and-drop scene composition;
- более широкий coverage `gprMax` commands через guided UI;
- библиотека антенн и import внешней геометрии;
- advanced raw-input workspace для power users.

### Принципы

- user simplicity first;
- сначала рабочий сценарий, потом глубина;
- UI не должен раскрывать внутреннюю сериализацию там, где можно говорить языком задачи;
- advanced возможности должны быть доступны, но не должны перегружать базовый поток работы;
- адаптивность и тестируемость важнее декоративной сложности.

## English

This document captures the staged UI evolution of `GPRMax Workbench` after the Stage 1-6 foundation.

### Goal

First deliver a convincing, testable desktop workspace for geophysicists and engineers, then gradually introduce richer editing and advanced tooling.

### UI Phase 1

Status: implemented in the current iteration.

Included:

- a more human-facing shell with persistent project context;
- a dashboard-style welcome screen;
- bundled example projects as part of the onboarding path;
- project and simulation summary tiles;
- more adaptive splitters and reflow on the key screens;
- a more coherent visual system with workstation-style cards and a restrained corporate palette.

### UI Phase 2

Next step after interface smoke testing:

- reshape the Model Editor around guided sections and user scenarios;
- clearly separate basic and advanced simulation flows;
- strengthen empty / loading / error / success states across the application;
- improve Results Viewer readability, including a clearer B-scan layout;
- add entity-aware inline help and warnings where users are likely to make mistakes.

### Feature Phase 3

Capabilities intentionally deferred until after the shell/UX iteration:

- 2D/3D canvas editing;
- drag-and-drop scene composition;
- broader guided coverage of `gprMax` commands;
- antenna libraries and external geometry import;
- an advanced raw-input workspace for power users.

### Principles

- user simplicity first;
- deliver a working workflow before deeper tooling;
- the UI should not expose internal serialization where task language is sufficient;
- advanced capabilities must remain available without overloading the base workflow;
- adaptability and testability matter more than decorative complexity.
