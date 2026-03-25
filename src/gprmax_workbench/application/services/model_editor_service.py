from __future__ import annotations

import copy
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TypeVar

from ...domain.model_entities import (
    default_antenna_model,
    default_geometry,
    default_geometry_import,
    default_material,
    default_receiver,
    default_source,
    default_waveform,
)
from ...domain.models import (
    AntennaModelDefinition,
    BUILTIN_MATERIAL_IDENTIFIERS,
    GeometryImportDefinition,
    GeometryPrimitive,
    MaterialDefinition,
    Project,
    ReceiverDefinition,
    SourceDefinition,
    Vector3,
    WaveformDefinition,
)
from ...domain.validation import ValidationResult, validate_project
from ..state import AppState

T = TypeVar("T")


@dataclass(slots=True)
class HistoryActionResult:
    applied: bool
    validation: ValidationResult | None = None
    context: object | None = None


@dataclass(slots=True)
class HistoryBatch:
    undo_context: object | None = None
    redo_context: object | None = None


@dataclass(slots=True)
class _HistoryEntry:
    before: Project
    after: Project
    undo_context: object | None = None
    redo_context: object | None = None


@dataclass(slots=True)
class _ActiveHistoryBatch:
    before: Project
    context: HistoryBatch


class ModelEditorService:
    """Applies editor mutations to the current project in memory."""

    def __init__(self, state: AppState) -> None:
        self._state = state
        self._undo_stack: list[_HistoryEntry] = []
        self._redo_stack: list[_HistoryEntry] = []
        self._tracked_project_id: int | None = None
        self._clean_index: int | None = 0
        self._active_history_batch: _ActiveHistoryBatch | None = None

    def current_project(self) -> Project | None:
        self._sync_history_target()
        return self._state.current_project

    def require_current_project(self) -> Project:
        project = self.current_project()
        if project is None:
            raise RuntimeError("No project is currently open.")
        return project

    def current_validation(self) -> ValidationResult:
        self._sync_history_target()
        return self._state.current_project_validation

    def can_undo(self) -> bool:
        self._sync_history_target()
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        self._sync_history_target()
        return bool(self._redo_stack)

    @contextmanager
    def history_batch(self) -> Iterator[HistoryBatch]:
        project = self.require_current_project()
        outermost = self._active_history_batch is None
        if outermost:
            self._active_history_batch = _ActiveHistoryBatch(
                before=copy.deepcopy(project),
                context=HistoryBatch(),
            )
        active_batch = self._active_history_batch
        if active_batch is None:
            raise RuntimeError("History batch was not initialized.")
        try:
            yield active_batch.context
        except Exception:
            if outermost:
                self._active_history_batch = None
                self._apply_snapshot(project, active_batch.before)
                validation = self._revalidate_project(project)
                self._update_dirty_flag()
                self._state.current_project_validation = validation
            raise
        else:
            if not outermost:
                return
            completed_batch = self._active_history_batch
            self._active_history_batch = None
            if completed_batch is None:
                return
            after = copy.deepcopy(project)
            validation = self._revalidate_project(project)
            if completed_batch.before != after:
                self._record_history(
                    completed_batch.before,
                    after,
                    completed_batch.context.undo_context,
                    completed_batch.context.redo_context,
                )
            self._update_dirty_flag()
            self._state.current_project_validation = validation

    def undo(self) -> HistoryActionResult:
        project = self.require_current_project()
        if not self._undo_stack:
            return HistoryActionResult(applied=False)

        entry = self._undo_stack.pop()
        self._apply_snapshot(project, entry.before)
        self._redo_stack.append(entry)
        validation = self._revalidate_project(project)
        self._update_dirty_flag()
        return HistoryActionResult(
            applied=True,
            validation=validation,
            context=entry.undo_context,
        )

    def redo(self) -> HistoryActionResult:
        project = self.require_current_project()
        if not self._redo_stack:
            return HistoryActionResult(applied=False)

        entry = self._redo_stack.pop()
        self._apply_snapshot(project, entry.after)
        self._undo_stack.append(entry)
        validation = self._revalidate_project(project)
        self._update_dirty_flag()
        return HistoryActionResult(
            applied=True,
            validation=validation,
            context=entry.redo_context,
        )

    def update_project_overview(
        self,
        *,
        project_name: str,
        description: str,
        model_title: str,
        model_notes: str,
        model_tags: Sequence[str],
        domain_size_m: Vector3,
        resolution_m: Vector3,
        time_window_s: float,
        scan_trace_count: int | None,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.metadata.name = project_name.strip()
            project.metadata.description = description.strip()
            project.model.title = model_title.strip()
            project.model.notes = model_notes.strip()
            project.model.tags = [item for item in model_tags if item]
            project.model.domain.size_m = domain_size_m
            project.model.domain.resolution_m = resolution_m
            project.model.domain.time_window_s = time_window_s
            project.model.scan_trace_count = scan_trace_count

        return self._mutate(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )

    def update_domain_size(
        self,
        size_m: Vector3,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.domain.size_m = size_m

        return self._mutate(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )

    def add_material(
        self,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            existing = [item.identifier for item in project.model.materials]
            material = default_material(len(project.model.materials) + 1)
            material.identifier = self._make_unique_name(material.identifier, existing)
            project.model.materials.append(material)
            return len(project.model.materials) - 1

        _, index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return index

    def update_material(
        self,
        index: int,
        material: MaterialDefinition,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.materials[index] = material

        return self._mutate(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )

    def duplicate_material(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            duplicate = copy.deepcopy(project.model.materials[index])
            duplicate.identifier = self._make_unique_name(
                duplicate.identifier or "material",
                [item.identifier for item in project.model.materials],
            )
            project.model.materials.insert(index + 1, duplicate)
            return index + 1

        _, new_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return new_index

    def delete_material(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int | None:
        def mutate(project: Project) -> int | None:
            del project.model.materials[index]
            if not project.model.materials:
                return None
            return min(index, len(project.model.materials) - 1)

        _, next_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return next_index

    def add_waveform(
        self,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            existing = [item.identifier for item in project.model.waveforms]
            waveform = default_waveform(len(project.model.waveforms) + 1)
            waveform.identifier = self._make_unique_name(waveform.identifier, existing)
            project.model.waveforms.append(waveform)
            return len(project.model.waveforms) - 1

        _, index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return index

    def update_waveform(
        self,
        index: int,
        waveform: WaveformDefinition,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.waveforms[index] = waveform

        return self._mutate(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )

    def duplicate_waveform(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            duplicate = copy.deepcopy(project.model.waveforms[index])
            duplicate.identifier = self._make_unique_name(
                duplicate.identifier or "waveform",
                [item.identifier for item in project.model.waveforms],
            )
            project.model.waveforms.insert(index + 1, duplicate)
            return index + 1

        _, new_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return new_index

    def delete_waveform(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int | None:
        def mutate(project: Project) -> int | None:
            del project.model.waveforms[index]
            if not project.model.waveforms:
                return None
            return min(index, len(project.model.waveforms) - 1)

        _, next_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return next_index

    def add_source(
        self,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            existing = [item.identifier for item in project.model.sources if item.identifier]
            source = default_source(project, len(project.model.sources) + 1)
            source.identifier = self._make_unique_name(source.identifier or "source", existing)
            project.model.sources.append(source)
            return len(project.model.sources) - 1

        _, index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return index

    def update_source(
        self,
        index: int,
        source: SourceDefinition,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.sources[index] = source

        return self._mutate(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )

    def duplicate_source(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            duplicate = copy.deepcopy(project.model.sources[index])
            duplicate.identifier = self._make_unique_name(
                duplicate.identifier or "source",
                [item.identifier for item in project.model.sources if item.identifier],
            )
            project.model.sources.insert(index + 1, duplicate)
            return index + 1

        _, new_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return new_index

    def delete_source(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int | None:
        def mutate(project: Project) -> int | None:
            del project.model.sources[index]
            if not project.model.sources:
                return None
            return min(index, len(project.model.sources) - 1)

        _, next_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return next_index

    def add_receiver(
        self,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            existing = [item.identifier for item in project.model.receivers if item.identifier]
            receiver = default_receiver(project, len(project.model.receivers) + 1)
            receiver.identifier = self._make_unique_name(
                receiver.identifier or "receiver",
                existing,
            )
            project.model.receivers.append(receiver)
            return len(project.model.receivers) - 1

        _, index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return index

    def update_receiver(
        self,
        index: int,
        receiver: ReceiverDefinition,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.receivers[index] = receiver

        return self._mutate(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )

    def duplicate_receiver(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            duplicate = copy.deepcopy(project.model.receivers[index])
            duplicate.identifier = self._make_unique_name(
                duplicate.identifier or "receiver",
                [item.identifier for item in project.model.receivers if item.identifier],
            )
            project.model.receivers.insert(index + 1, duplicate)
            return index + 1

        _, new_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return new_index

    def delete_receiver(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int | None:
        def mutate(project: Project) -> int | None:
            del project.model.receivers[index]
            if not project.model.receivers:
                return None
            return min(index, len(project.model.receivers) - 1)

        _, next_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return next_index

    def add_geometry(
        self,
        kind: str = "box",
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            existing = [item.label for item in project.model.geometry if item.label]
            geometry = default_geometry(project, len(project.model.geometry) + 1, kind=kind)
            geometry.label = self._make_unique_name(
                geometry.label or geometry.kind,
                existing,
            )
            project.model.geometry.append(geometry)
            return len(project.model.geometry) - 1

        _, index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return index

    def update_geometry(
        self,
        index: int,
        geometry: GeometryPrimitive,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.geometry[index] = geometry

        return self._mutate(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )

    def duplicate_geometry(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            duplicate = copy.deepcopy(project.model.geometry[index])
            duplicate.label = self._make_unique_name(
                duplicate.label or duplicate.kind,
                [item.label for item in project.model.geometry if item.label],
            )
            project.model.geometry.insert(index + 1, duplicate)
            return index + 1

        _, new_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return new_index

    def delete_geometry(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int | None:
        def mutate(project: Project) -> int | None:
            del project.model.geometry[index]
            if not project.model.geometry:
                return None
            return min(index, len(project.model.geometry) - 1)

        _, next_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return next_index

    def add_geometry_import(
        self,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            existing = [
                item.identifier for item in project.model.geometry_imports if item.identifier
            ]
            geometry_import = default_geometry_import(
                len(project.model.geometry_imports) + 1
            )
            geometry_import.identifier = self._make_unique_name(
                geometry_import.identifier,
                existing,
            )
            project.model.geometry_imports.append(geometry_import)
            return len(project.model.geometry_imports) - 1

        _, index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return index

    def update_geometry_import(
        self,
        index: int,
        geometry_import: GeometryImportDefinition,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.geometry_imports[index] = geometry_import

        return self._mutate(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )

    def duplicate_geometry_import(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            duplicate = copy.deepcopy(project.model.geometry_imports[index])
            duplicate.identifier = self._make_unique_name(
                duplicate.identifier or "geometry_import",
                [item.identifier for item in project.model.geometry_imports if item.identifier],
            )
            project.model.geometry_imports.insert(index + 1, duplicate)
            return index + 1

        _, new_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return new_index

    def delete_geometry_import(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int | None:
        def mutate(project: Project) -> int | None:
            del project.model.geometry_imports[index]
            if not project.model.geometry_imports:
                return None
            return min(index, len(project.model.geometry_imports) - 1)

        _, next_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return next_index

    def add_antenna_model(
        self,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            existing = [
                item.identifier for item in project.model.antenna_models if item.identifier
            ]
            antenna_model = default_antenna_model(
                project,
                len(project.model.antenna_models) + 1,
            )
            antenna_model.identifier = self._make_unique_name(
                antenna_model.identifier,
                existing,
            )
            project.model.antenna_models.append(antenna_model)
            return len(project.model.antenna_models) - 1

        _, index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return index

    def update_antenna_model(
        self,
        index: int,
        antenna_model: AntennaModelDefinition,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.antenna_models[index] = antenna_model

        return self._mutate(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )

    def duplicate_antenna_model(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int:
        def mutate(project: Project) -> int:
            duplicate = copy.deepcopy(project.model.antenna_models[index])
            duplicate.identifier = self._make_unique_name(
                duplicate.identifier or "antenna",
                [item.identifier for item in project.model.antenna_models if item.identifier],
            )
            project.model.antenna_models.insert(index + 1, duplicate)
            return index + 1

        _, new_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return new_index

    def delete_antenna_model(
        self,
        index: int,
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> int | None:
        def mutate(project: Project) -> int | None:
            del project.model.antenna_models[index]
            if not project.model.antenna_models:
                return None
            return min(index, len(project.model.antenna_models) - 1)

        _, next_index = self._mutate_with_result(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return next_index

    def update_advanced_workspace(
        self,
        *,
        python_blocks: Sequence[str],
        raw_input_overrides: Sequence[str],
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.python_blocks = [item for item in python_blocks if item.strip()]
            project.advanced_input_overrides = [
                item for item in raw_input_overrides if item.strip()
            ]

        return self._mutate(
            mutate,
            undo_context=undo_context,
            redo_context=redo_context,
        )

    def available_material_ids(self) -> list[str]:
        project = self.require_current_project()
        values = sorted(BUILTIN_MATERIAL_IDENTIFIERS) + [
            item.identifier for item in project.model.materials if item.identifier.strip()
        ]
        return list(dict.fromkeys(values))

    def available_waveform_ids(self) -> list[str]:
        project = self.require_current_project()
        return [item.identifier for item in project.model.waveforms if item.identifier.strip()]

    def _mutate(
        self,
        callback: Callable[[Project], None],
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> ValidationResult:
        validation, _ = self._mutate_with_result(
            callback,
            undo_context=undo_context,
            redo_context=redo_context,
        )
        return validation

    def _mutate_with_result(
        self,
        callback: Callable[[Project], T],
        *,
        undo_context: object | None = None,
        redo_context: object | None = None,
    ) -> tuple[ValidationResult, T]:
        project = self.require_current_project()
        if self._active_history_batch is not None:
            result = callback(project)
            validation = self._after_mutation(project)
            return validation, result

        before = copy.deepcopy(project)
        result = callback(project)
        after = copy.deepcopy(project)
        if before != after:
            validation = self._after_mutation(project)
            self._record_history(before, after, undo_context, redo_context)
            self._update_dirty_flag()
            return validation, result

        validation = self._revalidate_project(project)
        return validation, result

    def _after_mutation(self, project: Project) -> ValidationResult:
        validation = self._revalidate_project(project)
        self._state.current_project_dirty = True
        return validation

    def _revalidate_project(self, project: Project) -> ValidationResult:
        validation = validate_project(project)
        self._state.current_project_validation = validation
        return validation

    def _record_history(
        self,
        before: Project,
        after: Project,
        undo_context: object | None,
        redo_context: object | None,
    ) -> None:
        current_position = len(self._undo_stack)
        if self._clean_index is not None and self._clean_index > current_position:
            self._clean_index = None
        self._redo_stack.clear()
        self._undo_stack.append(
            _HistoryEntry(
                before=before,
                after=after,
                undo_context=undo_context,
                redo_context=redo_context,
            )
        )

    def _update_dirty_flag(self) -> None:
        clean_index = self._clean_index
        self._state.current_project_dirty = (
            clean_index is None or len(self._undo_stack) != clean_index
        )

    def _apply_snapshot(self, project: Project, snapshot: Project) -> None:
        project.root = snapshot.root
        project.metadata = copy.deepcopy(snapshot.metadata)
        project.model = copy.deepcopy(snapshot.model)
        project.advanced_input_overrides = copy.deepcopy(snapshot.advanced_input_overrides)

    def _sync_history_target(self) -> None:
        project = self._state.current_project
        project_id = id(project) if project is not None else None
        if project_id != self._tracked_project_id:
            self._tracked_project_id = project_id
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._clean_index = 0
            self._active_history_batch = None
            return

        if project is not None and not self._state.current_project_dirty:
            self._clean_index = len(self._undo_stack)

    def _make_unique_name(self, base: str, existing: Sequence[str]) -> str:
        normalized = base.strip() or "item"
        existing_set = {item for item in existing if item.strip()}
        if normalized not in existing_set:
            return normalized

        counter = 2
        while True:
            candidate = f"{normalized}_{counter}"
            if candidate not in existing_set:
                return candidate
            counter += 1
