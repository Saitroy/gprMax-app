# gprMax Workbench Performance Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove editor freezes caused by full scene rebuilds and repeated shell repolish during ordinary interaction.

**Architecture:** Keep full scene rebuilds for project replacement and structural edits. Use lightweight previews while numeric values are being edited, avoid the second scene rebuild in `ProjectView`, debounce cross-panel refresh work, and skip unchanged shell status updates.

**Tech Stack:** Python, PySide6 `QTimer`, Qt Graphics View, unittest/pytest

---

## File Map

- Modify: `src/gprmax_workbench/ui/widgets/model_editor/scene_canvas_panel.py`
- Modify: `src/gprmax_workbench/ui/views/project_view.py`
- Modify: `src/gprmax_workbench/ui/main_window.py`
- Test: `tests/test_scene_canvas_panel.py`
- Test: `tests/test_project_view_smoke.py`
- Create: `tests/test_main_window_refresh.py`

### Task 1: Preview Inspector Values Without Rebuilding The Scene

- [ ] **Step 1: Write failing tests**

Append to `tests/test_scene_canvas_panel.py`:

```python
    def test_geometry_size_typing_renders_preview_without_rebuilding_scene(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            project.model.materials = [
                MaterialDefinition(identifier="soil", relative_permittivity=4.0, conductivity=0.001)
            ]
            state = AppState(current_project=project, current_project_validation=validate_project(project))
            editor = ModelEditorService(state)
            panel = SceneCanvasPanel(LocalizationService("en"), editor, ValidationService(state))
            geometry_index = editor.add_geometry("box")
            panel.set_project(project)
            panel._set_selected_row("geometry", geometry_index)  # noqa: SLF001
            refresh_count = 0
            original_refresh = panel._refresh_scene  # noqa: SLF001

            def count_refresh() -> None:
                nonlocal refresh_count
                refresh_count += 1
                original_refresh()

            panel._refresh_scene = count_refresh  # type: ignore[method-assign]  # noqa: SLF001
            panel._size_x.setValue(0.4)  # noqa: SLF001

            self.assertEqual(refresh_count, 0)
            self.assertGreaterEqual(len(panel._preview_items), 1)  # noqa: SLF001

    def test_geometry_size_apply_commits_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            project.model.materials = [
                MaterialDefinition(identifier="soil", relative_permittivity=4.0, conductivity=0.001)
            ]
            state = AppState(current_project=project, current_project_validation=validate_project(project))
            editor = ModelEditorService(state)
            panel = SceneCanvasPanel(LocalizationService("en"), editor, ValidationService(state))
            geometry_index = editor.add_geometry("box")
            panel.set_project(project)
            panel._set_selected_row("geometry", geometry_index)  # noqa: SLF001
            panel._size_x.setValue(0.4)  # noqa: SLF001

            panel._apply_button.click()  # noqa: SLF001

            geometry = project.model.geometry[geometry_index]
            lower = geometry.parameters["lower_left_m"]
            upper = geometry.parameters["upper_right_m"]
            self.assertAlmostEqual(upper["x"] - lower["x"], 0.4, places=6)
```

- [ ] **Step 2: Verify the tests fail**

Run:

```powershell
python -m pytest tests/test_scene_canvas_panel.py -k "typing or size_apply" -v
```

Expected: the typing test fails because `_apply_entity_changes()` rebuilds the
scene immediately.

- [ ] **Step 3: Add lightweight preview wiring**

In `SceneCanvasPanel._build_detail_pages()`, connect size fields to a preview:

```python
        self._outputs_edit.editingFinished.connect(self._apply_entity_changes)
        for widget in (self._pos_x, self._pos_y, self._pos_z, self._size_x, self._size_y, self._size_z, self._radius):
            widget.valueChanged.connect(self._preview_entity_changes)
```

Keep combo boxes committed on selection. Add:

```python
    def _preview_entity_changes(self) -> None:
        if self._loading or not self._has_single_selection() or self._selected_entity_ref is None:
            return
        if self._selected_entity_ref.kind != "geometry" or self._project is None:
            return
        geometry = copy.deepcopy(self._project.model.geometry[self._selected_entity_ref.index])
        center = Vector3(self._pos_x.value(), self._pos_y.value(), self._pos_z.value())
        geometry = self._geometry_with_inspector_values(geometry, center)
        self._render_geometry_preview(geometry)
```

Extract the geometry mutation branch from `_apply_detail_changes()` into:

```python
    def _geometry_with_inspector_values(
        self,
        geometry: GeometryPrimitive,
        center: Vector3,
    ) -> GeometryPrimitive:
        material_id = str(self._material_combo.currentData() or "")
        geometry.material_ids = [material_id] if material_id else []
        if geometry.kind == "box":
            half_x = max(self._size_x.value(), 0.001) / 2
            half_y = max(self._size_y.value(), 0.001) / 2
            half_z = max(self._size_z.value(), 0.001) / 2
            geometry.parameters["lower_left_m"] = {"x": center.x - half_x, "y": center.y - half_y, "z": center.z - half_z}
            geometry.parameters["upper_right_m"] = {"x": center.x + half_x, "y": center.y + half_y, "z": center.z + half_z}
        elif geometry.kind == "sphere":
            geometry.parameters["center_m"] = {"x": center.x, "y": center.y, "z": center.z}
            geometry.parameters["radius_m"] = max(self._radius.value(), 0.001)
        elif geometry.kind == "cylinder":
            half_x = self._size_x.value() / 2
            half_y = self._size_y.value() / 2
            half_z = self._size_z.value() / 2
            geometry.parameters["start_m"] = {"x": center.x - half_x, "y": center.y - half_y, "z": center.z - half_z}
            geometry.parameters["end_m"] = {"x": center.x + half_x, "y": center.y + half_y, "z": center.z + half_z}
            geometry.parameters["radius_m"] = max(self._radius.value(), 0.001)
        return geometry
```

Use the helper inside `_apply_detail_changes()` before
`update_geometry(...)`. Remove the old direct `valueChanged` connections for
size and radius fields.

- [ ] **Step 4: Verify scene preview tests pass**

Run:

```powershell
python -m pytest tests/test_scene_canvas_panel.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/gprmax_workbench/ui/widgets/model_editor/scene_canvas_panel.py tests/test_scene_canvas_panel.py
git commit -m "perf: preview scene inspector edits without rebuild"
```

### Task 2: Avoid The Second Scene Rebuild

- [ ] **Step 1: Write a failing ProjectView test**

Append to `tests/test_project_view_smoke.py`:

```python
    def test_scene_originated_change_does_not_reload_scene_panel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            view = self._build_view(temp_dir)
            reload_count = 0
            original_set_project = view._scene_panel.set_project  # noqa: SLF001

            def count_reload(project) -> None:
                nonlocal reload_count
                reload_count += 1
                original_set_project(project)

            view._scene_panel.set_project = count_reload  # type: ignore[method-assign]  # noqa: SLF001
            view._scene_panel.model_changed.emit()  # noqa: SLF001

            self.assertEqual(reload_count, 0)
```

- [ ] **Step 2: Verify the test fails**

Run:

```powershell
python -m pytest tests/test_project_view_smoke.py::ProjectViewSmokeTests::test_scene_originated_change_does_not_reload_scene_panel -v
```

Expected: FAIL with `reload_count == 1`.

- [ ] **Step 3: Route scene changes through a lightweight handler**

In `ProjectView.__init__()`, connect non-scene panels to `_on_model_changed`
and connect the scene separately:

```python
        for panel in (
            self._general_panel,
            self._materials_panel,
            self._waveforms_panel,
            self._sources_panel,
            self._receivers_panel,
            self._geometry_panel,
            self._libraries_panel,
            self._advanced_panel,
        ):
            panel.model_changed.connect(self._on_model_changed)
        self._scene_panel.model_changed.connect(self._on_scene_model_changed)
```

Add:

```python
    def _on_scene_model_changed(self) -> None:
        self._on_model_changed(refresh_scene=False)

    def _on_model_changed(self, *, refresh_scene: bool = True) -> None:
        project = self._model_editor_service.current_project()
        validation = self._validation_service.current_validation()
        self._is_dirty = True
        if refresh_scene:
            self._scene_panel.set_project(project)
        self._refresh_after_model_change(project, validation)
        self.editor_changed.emit()
```

Move the existing panel validation refreshes, summary update, and
`_refresh_project_workspace(...)` into:

```python
    def _refresh_after_model_change(
        self,
        project: Project | None,
        validation: ValidationResult | None,
    ) -> None:
```

Do not call `self._scene_panel.set_project(project)` from this helper.

- [ ] **Step 4: Verify tests pass**

Run:

```powershell
python -m pytest tests/test_project_view_smoke.py tests/test_scene_canvas_panel.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/gprmax_workbench/ui/views/project_view.py tests/test_project_view_smoke.py
git commit -m "perf: avoid duplicate scene rebuild after canvas edits"
```

### Task 3: Skip Unchanged Sidebar Repolish

- [ ] **Step 1: Create a focused MainWindow regression test**

Create `tests/test_main_window_refresh.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gprmax_workbench.ui.main_window import MainWindow


class _FakeStyle:
    def __init__(self) -> None:
        self.polish_count = 0
        self.unpolish_count = 0

    def polish(self, _widget) -> None:
        self.polish_count += 1

    def unpolish(self, _widget) -> None:
        self.unpolish_count += 1


class _FakeLabel:
    def __init__(self) -> None:
        self._text = ""
        self._tooltip = ""
        self._properties: dict[str, object] = {}
        self._style = _FakeStyle()

    def text(self) -> str:
        return self._text

    def setText(self, text: str) -> None:  # noqa: N802
        self._text = text

    def setToolTip(self, text: str) -> None:  # noqa: N802
        self._tooltip = text

    def property(self, key: str) -> object:
        return self._properties.get(key)

    def setProperty(self, key: str, value: object) -> None:  # noqa: N802
        self._properties[key] = value

    def style(self) -> _FakeStyle:
        return self._style


def test_sidebar_status_skips_repolish_when_text_and_tone_are_unchanged() -> None:
    label = _FakeLabel()

    MainWindow._set_sidebar_status(object(), label, "Runtime ready", "success")  # type: ignore[arg-type]
    MainWindow._set_sidebar_status(object(), label, "Runtime ready", "success")  # type: ignore[arg-type]

    assert label.style().polish_count == 1
    assert label.style().unpolish_count == 1
```

- [ ] **Step 2: Verify the test fails**

Run:

```powershell
python -m pytest tests/test_main_window_refresh.py -v
```

Expected: FAIL because both calls repolish the label.

- [ ] **Step 3: Add the unchanged-state guard**

Replace `MainWindow._set_sidebar_status()` with:

```python
    def _set_sidebar_status(self, label: QLabel, text: str, tone: str) -> None:
        if label.text() == text and label.property("statusTone") == tone:
            return
        label.setText(text)
        label.setToolTip(text)
        label.setProperty("statusTone", tone)
        label.style().unpolish(label)
        label.style().polish(label)
```

- [ ] **Step 4: Verify phase 1**

Run:

```powershell
python -m pytest
python -m ruff check src tests
git diff --check
```

Expected: all commands exit with code `0`.

- [ ] **Step 5: Commit**

```powershell
git add src/gprmax_workbench/ui/main_window.py tests/test_main_window_refresh.py
git commit -m "perf: skip unchanged shell status repolish"
```
