# First Release Readiness

Last updated: 2026-04-16

## Scope

This document evaluates the repository against the needs of a first release.

Two release targets matter:

- `invited alpha`: a build for the core team or a small trusted design-partner group;
- `Alpha 0.3.0 Installer Candidate`: the next installer-first release path;
- `first public bundled release`: a release intended for outside users with a bundled `gprMax` runtime and a supported installation path.

## Short Verdict

- Invited alpha 0.2.1 UX-fix: `GO`, with explicit caveats.
- Alpha 0.3.0 Installer Candidate: `NOT READY YET`.
- First public bundled release: `NO-GO`.

The project is technically usable for guided testing, but Alpha 0.3.0 still needs a fresh bundle/installer rebuild, smoke test, clean-machine validation, and release asset pass. A broad public bundled release also needs compliance sign-off.

## Evidence Available Today

- The application has a working layered architecture with `ui`, `application`, `domain`, `infrastructure`, and `jobs`.
- The main user flow exists across `Welcome -> Project -> Simulation -> Results`.
- Runtime diagnostics and bundled-engine foundation work are present.
- Repository CI now exists in `.github/workflows/ci.yml`.
- Public release checklist, license-review checklist, issue templates, and support-bundle tooling now exist in the main repository.
- The repository currently contains `119` automated tests, and `.venv\Scripts\python.exe tools\run_tests.py` passes locally.
- The current desktop shell has been smoke-checked for `1366x768` and `1920x1080`.
- A full local dry-run of `packaging/windows/build_desktop_bundle.ps1` and `packaging/windows/build_installer.ps1` succeeded on 2026-04-10.
- Silent install, launch, and uninstall validation succeeded on the local Windows release machine on 2026-04-10.
- Alpha `0.2.1` now has an explicit UX sign-off scenario in `docs/ALPHA_0_2_UX_SIGNOFF.md`.

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
- the Alpha 0.2.x scenario still needs real tester feedback captured through GitHub Issues.

### 3. Codebase and Test Baseline

Status: `good for alpha`

Why:

- the architecture is modular and testable;
- there is meaningful unit-test coverage around services, viewers, and key UI smoke paths;
- the repository is already in a shape that contributors can run locally.

Remaining gaps:

- CI does not yet build the desktop bundle or installer artifact;
- release sign-off is still manual, even though the repository now contains explicit checklists.

### 4. Packaging and Installation

Status: `locally validated, not yet release-proven`

Why:

- the repository contains engine bundle build scripts under `packaging/engine/`;
- Stage 6 runtime resolution exists in the application.
- the repository now contains a Windows desktop bundle and installer pipeline under `packaging/windows/`.

Blocking gaps:

- Alpha `0.2.1` needs a fresh local bundle/installer rebuild before distribution;
- the new pipeline still needs a clean-machine or VM validation pass outside the maintainer workstation before Alpha `0.3.0`;
- there is no signed public artifact history yet;
- installer validation is still pending outside local repository checks.

### 5. Legal and Compliance

Status: `review-ready, sign-off pending`

Blocking facts:

- the project intends to bundle `gprMax`;
- `gprMax` is GPLv3+;
- the repository documentation already treats license review as a release gate;
- release-time inventory export now exists, but legal/compliance sign-off is still human work.

Conclusion:

- a first public bundled release should not ship before that review is completed and the release artifact includes the required notices and license texts.

### 6. Supportability and Operations

Status: `not ready`

Blocking gaps:

- support and reporting assets now exist, but they have not yet been exercised in a real outside-user support loop;
- the support-bundle script is not yet exposed directly inside the running GUI;
- release operations still need one full rehearsal from issue report to reproduced fix.

## Public Release Blockers

The following items should still be treated as blockers for the first public bundled release:

1. Run the new CI and packaging pipeline on the intended release path and keep the build green.
2. Rebuild the Alpha `0.2.1` desktop bundle and installer and run `packaging/windows/smoke_test_bundle.ps1`.
3. Validate the Alpha `0.3.0` desktop bundle and installer on a clean Windows machine or VM outside the maintainer workstation.
4. Complete GPL and bundled-license sign-off using `docs/BUNDLED_LICENSE_REVIEW.md` plus generated inventory artifacts.
5. Execute `docs/PUBLIC_RELEASE_CHECKLIST.md` end to end for a real release candidate.
6. Rehearse the support flow with issue templates and `tools/collect_support_bundle.py` on at least one real bug report.

## Recommended Non-Blocking Improvements

These are important, but they should not hold up an internal alpha:

- persist splitter sizes and selected workspace state;
- expand real-world runtime smoke testing;
- improve release-facing documentation with screenshots and short workflow guides;
- deepen simulation preflight and error copy;
- broaden command coverage in the guided editor.

## Recommended Release Sequence

1. Ship Alpha `0.2.1` as a UX-fix prerelease for guided testing.
2. Collect tester feedback through GitHub Issues and close blocking UX issues.
3. Cut Alpha `0.3.0` as the installer-first candidate with fresh bundle/installer smoke.
4. Run a small design-partner round on real Windows machines.
5. Cut the first public bundled release only after packaging, CI, and legal review are complete.

## Bottom Line

The repository is ready to behave like a serious internal alpha and design-partner prototype.

It is not yet ready for a first public bundled release.
