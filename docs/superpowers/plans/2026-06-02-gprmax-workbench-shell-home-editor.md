# gprMax Workbench Shell Home And Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved compact shell, quiet Home screen, and scene-first Model Editor.

**Architecture:** Reuse existing PySide6 views and services. Make the global sidebar a narrow rail, simplify Home to a small number of meaningful surfaces, and reshape the existing scene panel into layer rail, canvas, and contextual inspector columns.

**Tech Stack:** Python, PySide6 layouts and splitters, existing localization service, unittest/pytest

---

## File Map

- Modify: `src/gprmax_workbench/ui/main_window.py`
- Modify: `src/gprmax_workbench/ui/theme.py`
- Modify: `src/gprmax_workbench/ui/views/welcome_view.py`
- Modify: `src/gprmax_workbench/ui/views/project_view.py`
- Modify: `src/gprmax_workbench/ui/widgets/model_editor/scene_canvas_panel.py`
- Modify: `src/gprmax_workbench/application/services/localization_service.py`
- Test: `tests/test_welcome_view.py`
- Test: `tests/test_project_view_smoke.py`
- Test: `tests/test_scene_canvas_panel.py`
- Test: `tests/test_main_window_refresh.py`

### Task 1: Replace The Wide Sidebar With A Compact Navigation Rail

- [ ] **Step 1: Add failing shell geometry tests**

In `tests/test_main_window_refresh.py`, assert:

```python
def test_sidebar_is_a_compact_navigation_rail(main_window) -> None:
    assert main_window._sidebar.maximumWidth() <= 84  # noqa: SLF001
    assert main_window._sidebar.minimumWidth() >= 64  # noqa: SLF001
    assert main_window._sidebar_subtitle.isHidden()  # noqa: SLF001
```

- [ ] **Step 2: Verify failure**

Run:

```powershell
python -m pytest tests/test_main_window_refresh.py -k compact_navigation_rail -v
```

Expected: FAIL because the current sidebar is `196..252` pixels wide.

- [ ] **Step 3: Compact the shell**

In `MainWindow._build_sidebar()` use:

```python
        frame.setMinimumWidth(68)
        frame.setMaximumWidth(84)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(8)
        self._sidebar_title.setText("g")
        self._sidebar_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sidebar_subtitle.setVisible(False)
```

Keep navigation item tooltips from `_retranslate_navigation()`. Hide the
multi-line sidebar status area in the rail and expose Settings and
Documentation as tooltip-backed rail actions. Update
`_sidebar_width_for_window()`:

```python
    def _sidebar_width_for_window(self, _window_width: int) -> int:
        return 76
```

Add theme rules for a flat rail and centered selected navigation rows.

- [ ] **Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_main_window_refresh.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/gprmax_workbench/ui/main_window.py src/gprmax_workbench/ui/theme.py tests/test_main_window_refresh.py
git commit -m "feat: compact the global navigation rail"
```

### Task 2: Simplify Home

- [ ] **Step 1: Add failing Home composition tests**

Append to `tests/test_welcome_view.py`:

```python
    def test_home_prioritizes_actions_recent_projects_and_one_example(self) -> None:
        view = WelcomeView(LocalizationService("en"))
        self.assertFalse(view._hero_card.isHidden())  # noqa: SLF001
        self.assertFalse(view._recent_card.isHidden())  # noqa: SLF001
        self.assertFalse(view._runtime_card.isHidden())  # noqa: SLF001
        self.assertTrue(view._status_card.isHidden())  # noqa: SLF001
        self.assertTrue(view._quick_start_card.isHidden())  # noqa: SLF001

    def test_home_wide_layout_places_recent_projects_beside_runtime_and_example(self) -> None:
        view = WelcomeView(LocalizationService("en"))
        view.resize(1100, 760)
        view.show()
        self._app.processEvents()
        recent = view._dashboard_grid.getItemPosition(view._dashboard_grid.indexOf(view._recent_card))  # noqa: SLF001
        runtime = view._dashboard_grid.getItemPosition(view._dashboard_grid.indexOf(view._runtime_card))  # noqa: SLF001
        self.assertEqual(recent[:2], (0, 0))
        self.assertEqual(runtime[:2], (0, 1))
```

- [ ] **Step 2: Verify failure**

Run:

```powershell
python -m pytest tests/test_welcome_view.py -v
```

Expected: FAIL because status and quick-start cards remain visible.

- [ ] **Step 3: Apply the approved Home composition**

In `WelcomeView.__init__()` hide the redundant cards:

```python
        self._status_card.setVisible(False)
        self._quick_start_card.setVisible(False)
```

In `_reflow_cards()` use the approved two-column layout:

```python
        if self.width() >= 1040:
            self._dashboard_grid.addWidget(self._recent_card, 0, 0, 2, 1)
            self._dashboard_grid.addWidget(self._runtime_card, 0, 1)
            self._dashboard_grid.addWidget(self._examples_card, 1, 1)
            self._dashboard_grid.setColumnStretch(0, 2)
            self._dashboard_grid.setColumnStretch(1, 1)
        else:
            self._dashboard_grid.addWidget(self._recent_card, 0, 0)
            self._dashboard_grid.addWidget(self._runtime_card, 1, 0)
            self._dashboard_grid.addWidget(self._examples_card, 2, 0)
            self._dashboard_grid.setColumnStretch(0, 1)
```

Retitle the hero through RU and EN localization keys so it reads as a calm
entry point with Create and Open as the only primary actions.

- [ ] **Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_welcome_view.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/gprmax_workbench/ui/views/welcome_view.py src/gprmax_workbench/application/services/localization_service.py tests/test_welcome_view.py
git commit -m "feat: simplify the Home start screen"
```

### Task 3: Make The Scene The Default Editor Workspace

- [ ] **Step 1: Add failing ProjectView tests**

Append to `tests/test_project_view_smoke.py`:

```python
    def test_scene_workspace_hides_redundant_editor_overview_cards(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            view = self._build_view(temp_dir)
            self.assertTrue(view._validation_summary_card.isHidden())  # noqa: SLF001
            self.assertTrue(view._nav_card.isHidden())  # noqa: SLF001
            self.assertIs(view._section_stack.currentWidget(), view._scene_panel)  # noqa: SLF001

    def test_editor_sections_remain_available_from_scene_toolbar(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            view = self._build_view(temp_dir)
            self.assertGreaterEqual(len(view._section_buttons), 8)  # noqa: SLF001
            self.assertFalse(view._section_toolbar_card.isHidden())  # noqa: SLF001
```

- [ ] **Step 2: Verify failure**

Run:

```powershell
python -m pytest tests/test_project_view_smoke.py -k "redundant or scene_toolbar" -v
```

Expected: FAIL because the permanent context navigation card remains visible.

- [ ] **Step 3: Reduce permanent ProjectView chrome**

In `ProjectView.__init__()` keep the scene section selected by default, show
the compact section toolbar, and hide permanent overview surfaces:

```python
        project_card.setVisible(False)
        self._validation_summary_card.setVisible(False)
        self._nav_card.setVisible(False)
        self._section_toolbar_card.setVisible(True)
```

Keep validation state accessible through toolbar button tones and the scene
status. Keep `_select_section_key()` and `_section_nav` as the internal routing
mechanism so existing sections remain functional.

- [ ] **Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_project_view_smoke.py -v
```

Expected: PASS after updating old assertions that expected the nav card.

- [ ] **Step 5: Commit**

```powershell
git add src/gprmax_workbench/ui/views/project_view.py tests/test_project_view_smoke.py
git commit -m "feat: make scene the primary model editor workspace"
```

### Task 4: Build The Three-Column Engineering Scene

- [ ] **Step 1: Add failing SceneCanvasPanel layout tests**

Append to `tests/test_scene_canvas_panel.py`:

```python
    def test_scene_workspace_uses_layer_rail_canvas_and_inspector(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            state = AppState(current_project=project, current_project_validation=validate_project(project))
            panel = SceneCanvasPanel(LocalizationService("en"), ModelEditorService(state), ValidationService(state))
            panel.set_project(project)
            self.assertEqual(panel._workspace_splitter.count(), 3)  # noqa: SLF001
            self.assertIs(panel._workspace_splitter.widget(0), panel._layer_rail)  # noqa: SLF001
            self.assertIs(panel._workspace_splitter.widget(2), panel._side_scroll)  # noqa: SLF001

    def test_scene_inspector_can_collapse_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = default_project("Scene Demo", Path(temp_dir))
            state = AppState(current_project=project, current_project_validation=validate_project(project))
            panel = SceneCanvasPanel(LocalizationService("en"), ModelEditorService(state), ValidationService(state))
            panel.set_project(project)
            panel._toggle_inspector()  # noqa: SLF001
            self.assertTrue(panel._side_scroll.isHidden())  # noqa: SLF001
            panel._toggle_inspector()  # noqa: SLF001
            self.assertFalse(panel._side_scroll.isHidden())  # noqa: SLF001
```

- [ ] **Step 2: Verify failure**

Run:

```powershell
python -m pytest tests/test_scene_canvas_panel.py -k "layer_rail or inspector_can_collapse" -v
```

Expected: FAIL because the current workspace has two columns.

- [ ] **Step 3: Split layers from the contextual inspector**

In `SceneCanvasPanel.__init__()` create a narrow left rail that owns
`_entities_card`, and add it before `view_shell`:

```python
        self._layer_rail = QFrame()
        self._layer_rail.setObjectName("WorkbenchLayerRail")
        layer_rail_layout = QVBoxLayout(self._layer_rail)
        layer_rail_layout.setContentsMargins(8, 8, 8, 8)
        layer_rail_layout.setSpacing(8)
        layer_rail_layout.addWidget(self._entities_card, 1)
        self._layer_rail.setMinimumWidth(150)
        self._layer_rail.setMaximumWidth(220)

        self._workspace_splitter.addWidget(self._layer_rail)
        self._workspace_splitter.addWidget(view_shell)
        self._workspace_splitter.addWidget(self._side_scroll)
        self._workspace_splitter.setStretchFactor(0, 0)
        self._workspace_splitter.setStretchFactor(1, 1)
        self._workspace_splitter.setStretchFactor(2, 0)
```

Remove `_entities_card` from `_side_layout`. Add an inspector toggle button to
the scene toolbar:

```python
    def _toggle_inspector(self) -> None:
        self._side_scroll.setVisible(self._side_scroll.isHidden())
        self._refresh_workspace_splitter_sizes(force=True)
```

Update `_refresh_workspace_splitter_sizes()` so desktop widths assign a narrow
layer rail, the remaining center width, and a `280..360` pixel inspector.
Below `900` pixels, keep the layer rail narrow and stack the inspector only
when needed.

- [ ] **Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_scene_canvas_panel.py tests/test_project_view_smoke.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/gprmax_workbench/ui/widgets/model_editor/scene_canvas_panel.py src/gprmax_workbench/ui/theme.py tests/test_scene_canvas_panel.py
git commit -m "feat: add layer rail and contextual scene inspector"
```

### Task 5: Run Phase 2 Verification

- [ ] **Step 1: Run automated checks**

```powershell
python -m pytest
python -m ruff check src tests
git diff --check
```

Expected: all commands exit with code `0`.

- [ ] **Step 2: Render desktop screenshots**

Launch the app offscreen or interactively and inspect the four required
desktop sizes. Confirm that Home is calm, the scene dominates the editor, the
layer rail is compact, and the inspector remains usable.

- [ ] **Step 3: Commit screenshot script changes only if a reusable QA helper was added**

```powershell
git status --short
```

Expected: no generated screenshots staged.

