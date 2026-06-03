# gprMax Workbench Settings Diagnostics And QA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the humane desktop UI with plain-language diagnostics, consistent RU/EN text, responsive QA, and measurable interaction checks.

**Architecture:** Keep Settings compact and expose technical information only on demand. Extend existing tests instead of introducing a new UI framework, then run full desktop viewport and performance verification.

**Tech Stack:** Python, PySide6, existing localization catalog, unittest/pytest, ruff

---

## File Map

- Modify: `src/gprmax_workbench/ui/views/settings_view.py`
- Modify: `src/gprmax_workbench/ui/theme.py`
- Modify: `src/gprmax_workbench/application/services/localization_service.py`
- Test: `tests/test_settings_view.py`
- Test: `tests/test_localization_service.py`
- Create: `tests/test_ui_performance_smoke.py`
- Create: `scripts/render_ui_states.py`

### Task 1: Keep Technical Runtime Details Collapsed

- [ ] **Step 1: Add failing Settings tests**

Append to `tests/test_settings_view.py`:

```python
    def test_settings_shows_actionable_runtime_status_before_technical_paths(self) -> None:
        view = SettingsView(LocalizationService("en"))
        self.assertFalse(view._runtime_status_badge.isHidden())  # noqa: SLF001
        self.assertTrue(view._runtime_summary_label.isHidden())  # noqa: SLF001
        self.assertTrue(view._diagnostics_label.isHidden())  # noqa: SLF001

    def test_runtime_executable_is_hidden_outside_advanced_mode(self) -> None:
        view = SettingsView(LocalizationService("en"))
        self.assertFalse(view._runtime_edit.isEnabled())  # noqa: SLF001
```

- [ ] **Step 2: Verify current behavior**

Run:

```powershell
python -m pytest tests/test_settings_view.py -v
```

Expected: PASS for already-supported collapsed details. The checked behavior
must remain exactly: technical labels are hidden until their details buttons
are checked, and the runtime executable field is disabled until advanced mode
is checked.

- [ ] **Step 3: Tighten Settings spacing and theme**

Keep the three existing cards:

- general settings;
- current runtime;
- diagnostics.

In `_build_card()` use:

```python
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(7)
```

Keep technical labels selectable and collapsed. Add a visible next-step text
to the runtime status when health is false using RU and EN localization keys.

- [ ] **Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_settings_view.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/gprmax_workbench/ui/views/settings_view.py src/gprmax_workbench/ui/theme.py src/gprmax_workbench/application/services/localization_service.py tests/test_settings_view.py
git commit -m "feat: keep settings diagnostics compact and actionable"
```

### Task 2: Verify RU And EN Coverage For New UI Keys

- [ ] **Step 1: Add catalog parity test**

Append to `tests/test_localization_service.py`:

```python
def test_redesign_keys_exist_in_ru_and_en_catalogs() -> None:
    required_keys = [
        "simulation.section.history",
        "simulation.action.open_logs",
        "settings.runtime.next_step",
    ]
    for language in ("ru", "en"):
        localization = LocalizationService(language)
        for key in required_keys:
            assert localization.text(key) != key
```

- [ ] **Step 2: Run the test**

```powershell
python -m pytest tests/test_localization_service.py -v
```

Expected: PASS after Tasks 1 and phase 3 add the matching RU and EN strings.

- [ ] **Step 3: Commit**

```powershell
git add src/gprmax_workbench/application/services/localization_service.py tests/test_localization_service.py
git commit -m "test: verify redesign localization coverage"
```

### Task 3: Add A Reusable UI Performance Smoke Test

- [ ] **Step 1: Create `tests/test_ui_performance_smoke.py`**

Use an offscreen Qt scene with many receivers and measure a single inspector
preview:

```python
from __future__ import annotations

import os
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gprmax_workbench.application.services.localization_service import LocalizationService
from gprmax_workbench.application.services.model_editor_service import ModelEditorService
from gprmax_workbench.application.services.validation_service import ValidationService
from gprmax_workbench.application.state import AppState
from gprmax_workbench.domain.models import MaterialDefinition, default_project
from gprmax_workbench.domain.validation import validate_project
from gprmax_workbench.ui.widgets.model_editor.scene_canvas_panel import SceneCanvasPanel


def test_large_scene_inspector_preview_stays_lightweight(tmp_path: Path) -> None:
    QApplication.instance() or QApplication([])
    project = default_project("Large scene", tmp_path)
    project.model.materials = [
        MaterialDefinition(identifier="soil", relative_permittivity=4.0, conductivity=0.001)
    ]
    state = AppState(current_project=project, current_project_validation=validate_project(project))
    editor = ModelEditorService(state)
    geometry_index = editor.add_geometry("box")
    for _index in range(300):
        editor.add_receiver()
    panel = SceneCanvasPanel(LocalizationService("en"), editor, ValidationService(state))
    panel.set_project(project)
    panel._set_selected_row("geometry", geometry_index)  # noqa: SLF001
    started = time.perf_counter()
    panel._size_x.setValue(0.45)  # noqa: SLF001
    elapsed_ms = (time.perf_counter() - started) * 1000
    assert elapsed_ms < 35
    assert len(panel._preview_items) >= 1  # noqa: SLF001
```

- [ ] **Step 2: Run the smoke test**

```powershell
python -m pytest tests/test_ui_performance_smoke.py -v
```

Expected: PASS on the local desktop used for UI QA. Keep the threshold at
`35 ms`; when the local machine cannot meet it, stop and investigate whether
`_refresh_scene()` or another full rebuild is still running during preview.

- [ ] **Step 3: Commit**

```powershell
git add tests/test_ui_performance_smoke.py
git commit -m "test: add large scene interaction smoke check"
```

### Task 4: Add Desktop Screenshot Rendering

- [ ] **Step 1: Create `scripts/render_ui_states.py`**

Create the script with this content:

```python
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from gprmax_workbench.app import build_context
from gprmax_workbench.ui.main_window import MainWindow
from gprmax_workbench.ui.theme import apply_theme


VIEWPORTS = (
    (1366, 768),
    (1440, 900),
    (1920, 1080),
    (2560, 1440),
)

PAGES = (
    ("home", "page.welcome.title"),
    ("model", "page.project.title"),
    ("simulation", "page.simulation.title"),
    ("results", "page.results.title"),
)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app)
    context = build_context()
    window = MainWindow(context)
    target = Path("artifacts/ui-redesign/final")
    target.mkdir(parents=True, exist_ok=True)

    for width, height in VIEWPORTS:
        window.resize(width, height)
        window.show()
        app.processEvents()
        for page_name, title_key in PAGES:
            page_index = window._page_index_by_title_key[title_key]  # noqa: SLF001
            window._show_page(page_index)  # noqa: SLF001
            app.processEvents()
            output = target / f"{width}x{height}-{page_name}.png"
            window.grab().save(str(output))

    window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the renderer**

```powershell
python scripts/render_ui_states.py
```

Expected: sixteen PNG files under `artifacts/ui-redesign/final`.

- [ ] **Step 3: Inspect screenshots**

Confirm:

- no clipped primary actions;
- scene remains dominant;
- layer rail and inspector remain readable;
- Home does not regress into a card wall;
- Simulation readiness remains visible;
- Results plot is larger than the surrounding panels;
- status colors and text remain consistent.

- [ ] **Step 4: Commit the reusable renderer**

```powershell
git add scripts/render_ui_states.py
git commit -m "test: add desktop UI screenshot renderer"
```

### Task 5: Run Final Verification

- [ ] **Step 1: Run complete checks**

```powershell
python -m pytest
python -m ruff check src tests scripts
git diff --check
```

Expected: all commands exit with code `0`.

- [ ] **Step 2: Run the application**

```powershell
python -m gprmax_workbench.main
```

Expected: the desktop application opens. Verify Home, Model, Simulation,
Results, Settings, RU/EN switching, scene mouse editing, numeric preview,
numeric apply, blocked simulation, completed result display, and inspector
collapse.

- [ ] **Step 3: Review changed files**

```powershell
git status --short
git diff --stat HEAD~1..HEAD
```

Expected: no generated runtime data, screenshots, or cache files are staged.
