# Model Editor MVP

## Scope

The Stage 4 model editor is a guided, form-based MVP for the most useful `gprMax` modelling subset.

Supported now:

- general model setup: title, domain size, `dx_dy_dz`, `time_window`;
- materials;
- waveforms;
- sources;
- receivers;
- geometry subset: `box`, `sphere`, `cylinder`;
- generated input preview from the current in-memory model.

Deferred intentionally:

- 2D/3D canvas editing;
- drag-and-drop scene composition;
- broad coverage of every `gprMax` command;
- antenna libraries and external geometry import;
- full advanced raw-input IDE.

## UX structure

The editor uses tabs at the top level and list-detail editing inside entity sections.

Why this shape:

- top-level tabs keep the workflow legible for non-programmers;
- list-detail panels scale better than one giant form;
- the MVP stays extensible without pretending to be a finished CAD environment.

Current tabs:

- `General`
- `Materials`
- `Waveforms`
- `Sources`
- `Receivers`
- `Geometry`
- `Input Preview`

## Data and service boundaries

The editor works against the typed project model already introduced in Stage 2 and extended in Stage 4.

Rules:

- widgets mutate project state through `ModelEditorService`;
- validation stays in the domain/application layer;
- input preview is generated through `InputPreviewService`;
- save/load flows remain owned by workspace/project services;
- simulation execution remains owned by the Stage 3 runner.

## Validation strategy

The editor validates both local field quality and cross-entity references.

Examples:

- positive domain and resolution values;
- unique material and waveform identifiers;
- sources referencing known waveforms;
- geometry referencing known materials;
- coordinates staying inside the domain;
- basic shape-specific constraints such as positive radius and ordered box bounds.

## Stage 4 to Stage 5 handoff

After Stage 4, the project has the minimum editor foundation needed for real user workflows:

1. create or open a project;
2. edit the model through forms;
3. review validation issues;
4. preview the generated input;
5. save;
6. run through the existing Stage 3 simulation view.

Stage 5 can now focus on results browsing without first inventing a usable model-authoring flow.
