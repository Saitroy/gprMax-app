# First Release Readiness

Last updated: 2026-04-07

## Scope

This document evaluates the repository against the needs of a first release.

Two release targets matter:

- `internal alpha`: a build for the core team or a small design-partner group;
- `first public bundled release`: a release intended for outside users with a bundled `gprMax` runtime and a supported installation path.

## Short Verdict

- Internal alpha: `GO`, with explicit caveats.
- First public bundled release: `NO-GO`.

The project is technically usable for guided testing, but it does not yet have the packaging, release, compliance, and operational support needed for a public bundled release.

## Evidence Available Today

- The application has a working layered architecture with `ui`, `application`, `domain`, `infrastructure`, and `jobs`.
- The main user flow exists across `Welcome -> Project -> Simulation -> Results`.
- Runtime diagnostics and bundled-engine foundation work are present.
- The repository currently contains `107` automated tests, and `python -m unittest discover tests` passes locally.
- The current desktop shell has been smoke-checked for `1366x768` and `1920x1080`.

## Readiness Assessment

### 1. Core Product Workflow

Status: `mostly ready`

Why:

- project creation/opening exists;
- model editing exists through guided sections;
- simulation orchestration exists with live logs and history;
- results browsing exists with A-scan and bounded B-scan support.

Remaining gaps:

- command coverage is still partial relative to the broader `gprMax` surface;
- some advanced analysis/export workflows are still intentionally limited.

### 2. UI Stability and Usability

Status: `mostly ready for alpha`

Why:

- the welcome page is present and functional;
- the main workspaces are separated instead of overloaded into one screen;
- splitter-based desktop layouts are in place;
- current geometry work targets common desktop sizes.

Remaining gaps:

- splitter sizes and workspace layout are not persisted yet;
- broader manual testing on real user hardware is still needed.

### 3. Codebase and Test Baseline

Status: `good for alpha`

Why:

- the architecture is modular and testable;
- there is meaningful unit-test coverage around services, viewers, and key UI smoke paths;
- the repository is already in a shape that contributors can run locally.

Remaining gaps:

- there is no repository-level CI workflow in the main `.github/workflows` path;
- release gates are currently social/manual rather than enforced by automation.

### 4. Packaging and Installation

Status: `not ready`

Why:

- the repository contains engine bundle build scripts under `packaging/engine/`;
- Stage 6 runtime resolution exists in the application.

Blocking gaps:

- there is no finished installer pipeline in the main repository;
- there is no documented release artifact assembly process for the desktop app itself;
- there is no signed, reproducible public release path yet.

### 5. Legal and Compliance

Status: `not ready`

Blocking facts:

- the project intends to bundle `gprMax`;
- `gprMax` is GPLv3+;
- the repository documentation already treats license review as a release gate.

Conclusion:

- a first public bundled release should not ship before that review is completed and the release artifact includes the required notices and license texts.

### 6. Supportability and Operations

Status: `not ready`

Blocking gaps:

- no main-repo CI workflow;
- no issue templates in the main repository;
- no documented crash/log bundle process for outside users;
- no public release checklist or sign-off flow existed before this assessment.

## Public Release Blockers

The following items should be treated as blockers for the first public bundled release:

1. Finish a repeatable installer/release artifact pipeline for the desktop app plus bundled engine.
2. Add repository CI for tests and at least one basic lint/type gate.
3. Complete GPL and bundled-license review for the intended distribution model.
4. Define a public release checklist with smoke tests, artifact validation, and sign-off.
5. Add minimum supportability assets: issue templates, bug-report instructions, and log collection guidance.

## Recommended Non-Blocking Improvements

These are important, but they should not hold up an internal alpha:

- persist splitter sizes and selected workspace state;
- expand real-world runtime smoke testing;
- improve release-facing documentation with screenshots and short workflow guides;
- deepen simulation preflight and error copy;
- broaden command coverage in the guided editor.

## Recommended Release Sequence

1. Ship an `internal alpha` tag for guided testing with the current desktop workspaces.
2. Close the public-release blockers above.
3. Run a small design-partner or invited beta round on real Windows machines.
4. Cut the first public bundled release only after packaging, CI, and legal review are complete.

## Bottom Line

The repository is ready to behave like a serious internal alpha and design-partner prototype.

It is not yet ready for a first public bundled release.
