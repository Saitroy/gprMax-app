# gprMax Workbench Simulation And Results Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Simulation and Results into a short, readable route from model readiness to graph analysis.

**Architecture:** Preserve run configuration, preview, logs, history, A-scan, B-scan, and artifacts. Reduce permanent navigation, keep advanced run controls collapsed, and give the primary result plot the largest area.

**Tech Stack:** Python, PySide6 layouts and splitters, Qt Charts widgets already in the repository, unittest/pytest

---

## File Map

- Modify: `src/gprmax_workbench/ui/views/simulation_view.py`
- Modify: `src/gprmax_workbench/ui/views/results_view.py`
- Modify: `src/gprmax_workbench/ui/theme.py`
- Modify: `src/gprmax_workbench/application/services/localization_service.py`
- Test: `tests/test_simulation_view.py`
- Test: `tests/test_results_view.py`

### Task 1: Collapse Simulation Into Setup Monitor And History

- [ ] **Step 1: Add failing navigation tests**

Append to `tests/test_simulation_view.py`:

```python
    def test_simulation_primary_navigation_contains_setup_monitor_and_history(self) -> None:
        view = SimulationView(localization=LocalizationService("en"), runtime_label="Bundled runtime")
        labels = [view._section_nav.item(row).text() for row in range(view._section_nav.count())]  # noqa: SLF001
        self.assertEqual(labels, ["Setup", "Run monitor", "History"])

    def test_preview_and_logs_remain_available_as_secondary_actions(self) -> None:
        view = SimulationView(localization=LocalizationService("en"), runtime_label="Bundled runtime")
        self.assertFalse(view._preview_button.isHidden())  # noqa: SLF001
        self.assertFalse(view._open_logs_button.isHidden())  # noqa: SLF001
```

- [ ] **Step 2: Verify failure**

Run:

```powershell
python -m pytest tests/test_simulation_view.py -k "primary_navigation or secondary_actions" -v
```

Expected: FAIL because preview and logs are currently permanent sections.

- [ ] **Step 3: Change the visible section list**

Keep `_preview_page` and `_log_page` in `_section_stack`, but expose only:

```python
        self._sections = [
            "simulation.section.launch",
            "simulation.section.monitor",
            "simulation.section.history",
        ]
```

Add a history page containing `_run_history`. Add `_open_logs_button` beside
monitor actions and connect it to a helper that opens `_log_page`. Keep preview
opened from `_preview_button`. Add RU and EN localization keys:

```python
"simulation.section.history": "History"
"simulation.action.open_logs": "Open logs"
```

Use the matching Russian strings in the RU catalog.

- [ ] **Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_simulation_view.py -v
```

Expected: PASS after updating section-state tests to use History instead of
permanent Preview and Logs rows.

- [ ] **Step 5: Commit**

```powershell
git add src/gprmax_workbench/ui/views/simulation_view.py src/gprmax_workbench/application/services/localization_service.py tests/test_simulation_view.py
git commit -m "feat: simplify simulation workflow navigation"
```

### Task 2: Keep Readiness Beside Configuration

- [ ] **Step 1: Add a failing layout assertion**

Append to `tests/test_simulation_view.py`:

```python
    def test_setup_keeps_configuration_main_and_readiness_compact(self) -> None:
        view = SimulationView(localization=LocalizationService("en"), runtime_label="Bundled runtime")
        view.resize(1200, 760)
        view.show()
        self._app.processEvents()
        sizes = view._top_splitter.sizes()  # noqa: SLF001
        self.assertGreater(sizes[1], sizes[0])
```

- [ ] **Step 2: Verify failure or capture the current ratio**

Run:

```powershell
python -m pytest tests/test_simulation_view.py -k readiness_compact -v
```

Expected: FAIL if the current status/config ratio is balanced or reversed.

- [ ] **Step 3: Set the approved desktop ratio**

In `_refresh_responsive_layout()` use a compact readiness side panel:

```python
            elif wide:
                readiness_width = max(260, min(340, int(self.width() * 0.28)))
                self._apply_splitter_sizes(
                    self._top_splitter,
                    [readiness_width, max(520, self.width() - readiness_width)],
                )
```

Place advanced MPI, restart, benchmark, and extra arguments behind the
existing `set_advanced_mode(True)` behavior.

- [ ] **Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_simulation_view.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/gprmax_workbench/ui/views/simulation_view.py tests/test_simulation_view.py
git commit -m "feat: prioritize simulation configuration and readiness"
```

### Task 3: Give Results More Space For The Plot

- [ ] **Step 1: Add failing Results layout tests**

Append to `tests/test_results_view.py`:

```python
    def test_results_desktop_keeps_run_list_narrow_and_plot_dominant(self) -> None:
        summary = _build_run_summary(Path("D:/demo/output/run1.out"))
        metadata = _build_metadata(summary.output_files[0], components=["Ez"])
        traces = _build_traces(summary.output_files[0].path, components=["Ez"])
        view, _results_service = _build_view([summary], metadata=metadata, traces=traces)
        view.resize(1200, 760)
        view.show()
        self._app.processEvents()
        run_width, plot_width = view._bottom_splitter.sizes()  # noqa: SLF001
        self.assertLessEqual(run_width, 210)
        self.assertGreater(plot_width, run_width * 2)

    def test_results_details_panel_is_compact_on_desktop(self) -> None:
        summary = _build_run_summary(Path("D:/demo/output/run1.out"))
        metadata = _build_metadata(summary.output_files[0], components=["Ez"])
        traces = _build_traces(summary.output_files[0].path, components=["Ez"])
        view, _results_service = _build_view([summary], metadata=metadata, traces=traces)
        view.resize(1400, 800)
        view.show()
        self._app.processEvents()
        main_width, details_width = view._page_splitter.sizes()  # noqa: SLF001
        self.assertLessEqual(details_width, 280)
        self.assertGreater(main_width, details_width * 2)
```

- [ ] **Step 2: Verify failure**

Run:

```powershell
python -m pytest tests/test_results_view.py -k "plot_dominant or details_panel_is_compact" -v
```

Expected: FAIL because the current panels reserve more width.

- [ ] **Step 3: Apply compact splitter defaults**

In `ResultsView._refresh_responsive_layout()` use:

```python
            elif main_orientation == Qt.Orientation.Horizontal:
                left_width = max(156, min(210, int(self.width() * 0.16)))
                self._apply_splitter_sizes(
                    self._bottom_splitter,
                    [left_width, max(620, self.width() - left_width - 280)],
                )
```

For desktop details:

```python
            elif page_orientation == Qt.Orientation.Horizontal:
                details_width = max(220, min(280, int(self.width() * 0.19)))
                self._apply_splitter_sizes(
                    self._page_splitter,
                    [max(720, self.width() - details_width), details_width],
                )
```

Keep A-scan as the first tab. Keep B-scan, summary, artifacts, and file open
actions intact.

- [ ] **Step 4: Verify**

Run:

```powershell
python -m pytest tests/test_results_view.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/gprmax_workbench/ui/views/results_view.py tests/test_results_view.py
git commit -m "feat: make results visualization dominant"
```

### Task 4: Run Phase 3 Verification

- [ ] **Step 1: Run automated checks**

```powershell
python -m pytest
python -m ruff check src tests
git diff --check
```

Expected: all commands exit with code `0`.

- [ ] **Step 2: Inspect Simulation and Results screenshots**

At the four required desktop sizes verify:

- Setup has one obvious Start action.
- A blocked Start explains why it is blocked.
- Monitor shows progress, concise status, cancel, and output-folder actions.
- Results opens on A-scan with a large plot.
- B-scan and artifacts remain accessible.

