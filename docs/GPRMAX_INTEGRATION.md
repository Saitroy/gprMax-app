# gprMax Integration

## Stage 3 scope

Stage 3 implements the first reliable execution layer between the desktop application and `gprMax`.

Implemented now:

- typed run configuration;
- `gprMax` command builder;
- subprocess-first adapter;
- input generation from the project model;
- per-run artifact folders;
- live stdout/stderr capture;
- persisted run metadata and history;
- UI actions for preview, export, start, cancel, and opening run/output folders.

Not implemented yet:

- full `gprMax` command coverage;
- advanced MPI/HPC orchestration;
- rich results parsing;
- retry, timeout, or queue scheduling policies beyond a single active run.

## Documented `gprMax` capabilities that directly shape Stage 3

- only `#domain`, `#dx_dy_dz`, and `#time_window` are essential for a model to run, so Stage 3 validation blocks on those and keeps missing sources/receivers as warnings;
- `--geometry-only` is supported directly as a runner mode;
- GPU execution is exposed through `-gpu`;
- model batching and restart hooks are exposed through `-n` and `-restart`;
- future MPI support is reflected in `-mpi` and `--mpi-no-spawn` fields, even though Stage 3 does not orchestrate MPI workflows yet.

## Command building

The command builder produces argument arrays, not concatenated shell strings.

Typical command:

```text
python -m gprMax <input-file> [flags...]
```

The builder currently knows about:

- `--geometry-only`
- `-gpu [ids...]`
- `--geometry-fixed`
- `--write-processed`
- `-benchmark`
- `-n`
- `-restart`
- `-mpi`
- `--mpi-no-spawn`

## Input generation subset

Current generator coverage:

- `#title`
- `#messages`
- `#domain`
- `#dx_dy_dz`
- `#time_window`
- `#pml_cells`
- `#output_dir`
- `#material`
- `#waveform`
- `#hertzian_dipole`
- `#magnetic_dipole`
- `#voltage_source`
- `#rx`
- `#box`
- `#sphere`
- `#cylinder`
- `#geometry_view`
- raw advanced overrides

Unsupported entities fail early with a clear generation error instead of silently producing a broken input file.

## Run lifecycle

Run statuses:

- `pending`
- `preparing`
- `running`
- `completed`
- `failed`
- `cancelled`

Flow:

1. validate project and run configuration;
2. create run artifact folders and metadata manifest;
3. generate and write `simulation.in`;
4. build the `gprMax` CLI command;
5. launch the subprocess;
6. stream stdout/stderr into logs and UI buffers;
7. persist completion status, exit code, and output file inventory.

## Deferred items

- broader geometry/object support;
- formal support matrix for GPU/MPI combinations;
- timeout policies;
- multi-run queue scheduling;
- results parsers built on top of the run artifact layout.
