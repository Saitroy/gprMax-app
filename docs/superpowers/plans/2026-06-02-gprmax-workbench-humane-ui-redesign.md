# gprMax Workbench Humane UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the approved compact PySide6 engineering workbench without removing existing gprMax capabilities.

**Architecture:** Implement the redesign as four independently testable phases. Stabilize interaction performance first, then reshape the shell and primary editor, then simplify the simulation and results workflow, and finally polish diagnostics, localization, and desktop viewport behavior.

**Tech Stack:** Python 3.11+, PySide6, Qt Graphics View, unittest/pytest, ruff

---

## Approved Design Reference

Read before implementation:

- `docs/superpowers/specs/2026-06-02-gprmax-workbench-humane-ui-redesign-design.md`
- `docs/design-audit/07-design-requirements.md`
- `docs/design-audit/08-redesign-roadmap.md`

## Execution Order

1. `docs/superpowers/plans/2026-06-02-gprmax-workbench-performance-foundation.md`
2. `docs/superpowers/plans/2026-06-02-gprmax-workbench-shell-home-editor.md`
3. `docs/superpowers/plans/2026-06-02-gprmax-workbench-simulation-results.md`
4. `docs/superpowers/plans/2026-06-02-gprmax-workbench-settings-qa.md`

Each phase ends with a working application, targeted tests, a full test run, and
one or more small commits. Do not combine phases into one large patch.

## Shared Verification Commands

Run after every phase:

```powershell
python -m pytest
python -m ruff check src tests
git diff --check
```

Expected: all commands exit with code `0`.

## Visual QA Rule

After phases 2, 3, and 4, render or launch the PySide6 application and inspect:

- `1366x768`
- `1440x900`
- `1920x1080`
- `2560x1440`

Record screenshots under `artifacts/ui-redesign/<phase>/`. Keep generated
screenshots out of commits unless the repository explicitly adopts them as
review artifacts.

