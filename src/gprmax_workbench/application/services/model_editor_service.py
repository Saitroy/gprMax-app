from __future__ import annotations

import copy
from collections.abc import Callable, Sequence

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


class ModelEditorService:
    """Applies editor mutations to the current project in memory."""

    def __init__(self, state: AppState) -> None:
        self._state = state

    def current_project(self) -> Project | None:
        return self._state.current_project

    def require_current_project(self) -> Project:
        project = self.current_project()
        if project is None:
            raise RuntimeError("No project is currently open.")
        return project

    def current_validation(self) -> ValidationResult:
        return self._state.current_project_validation

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

        return self._mutate(mutate)

    def add_material(self) -> int:
        project = self.require_current_project()
        existing = [item.identifier for item in project.model.materials]
        material = default_material(len(project.model.materials) + 1)
        material.identifier = self._make_unique_name(material.identifier, existing)
        project.model.materials.append(material)
        self._after_mutation(project)
        return len(project.model.materials) - 1

    def update_material(self, index: int, material: MaterialDefinition) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.materials[index] = material

        return self._mutate(mutate)

    def duplicate_material(self, index: int) -> int:
        project = self.require_current_project()
        duplicate = copy.deepcopy(project.model.materials[index])
        duplicate.identifier = self._make_unique_name(
            duplicate.identifier or "material",
            [item.identifier for item in project.model.materials],
        )
        project.model.materials.insert(index + 1, duplicate)
        self._after_mutation(project)
        return index + 1

    def delete_material(self, index: int) -> int | None:
        project = self.require_current_project()
        del project.model.materials[index]
        self._after_mutation(project)
        if not project.model.materials:
            return None
        return min(index, len(project.model.materials) - 1)

    def add_waveform(self) -> int:
        project = self.require_current_project()
        existing = [item.identifier for item in project.model.waveforms]
        waveform = default_waveform(len(project.model.waveforms) + 1)
        waveform.identifier = self._make_unique_name(waveform.identifier, existing)
        project.model.waveforms.append(waveform)
        self._after_mutation(project)
        return len(project.model.waveforms) - 1

    def update_waveform(self, index: int, waveform: WaveformDefinition) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.waveforms[index] = waveform

        return self._mutate(mutate)

    def duplicate_waveform(self, index: int) -> int:
        project = self.require_current_project()
        duplicate = copy.deepcopy(project.model.waveforms[index])
        duplicate.identifier = self._make_unique_name(
            duplicate.identifier or "waveform",
            [item.identifier for item in project.model.waveforms],
        )
        project.model.waveforms.insert(index + 1, duplicate)
        self._after_mutation(project)
        return index + 1

    def delete_waveform(self, index: int) -> int | None:
        project = self.require_current_project()
        del project.model.waveforms[index]
        self._after_mutation(project)
        if not project.model.waveforms:
            return None
        return min(index, len(project.model.waveforms) - 1)

    def add_source(self) -> int:
        project = self.require_current_project()
        existing = [item.identifier for item in project.model.sources if item.identifier]
        source = default_source(project, len(project.model.sources) + 1)
        source.identifier = self._make_unique_name(source.identifier or "source", existing)
        project.model.sources.append(source)
        self._after_mutation(project)
        return len(project.model.sources) - 1

    def update_source(self, index: int, source: SourceDefinition) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.sources[index] = source

        return self._mutate(mutate)

    def duplicate_source(self, index: int) -> int:
        project = self.require_current_project()
        duplicate = copy.deepcopy(project.model.sources[index])
        duplicate.identifier = self._make_unique_name(
            duplicate.identifier or "source",
            [item.identifier for item in project.model.sources if item.identifier],
        )
        project.model.sources.insert(index + 1, duplicate)
        self._after_mutation(project)
        return index + 1

    def delete_source(self, index: int) -> int | None:
        project = self.require_current_project()
        del project.model.sources[index]
        self._after_mutation(project)
        if not project.model.sources:
            return None
        return min(index, len(project.model.sources) - 1)

    def add_receiver(self) -> int:
        project = self.require_current_project()
        existing = [item.identifier for item in project.model.receivers if item.identifier]
        receiver = default_receiver(project, len(project.model.receivers) + 1)
        receiver.identifier = self._make_unique_name(
            receiver.identifier or "receiver",
            existing,
        )
        project.model.receivers.append(receiver)
        self._after_mutation(project)
        return len(project.model.receivers) - 1

    def update_receiver(
        self,
        index: int,
        receiver: ReceiverDefinition,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.receivers[index] = receiver

        return self._mutate(mutate)

    def duplicate_receiver(self, index: int) -> int:
        project = self.require_current_project()
        duplicate = copy.deepcopy(project.model.receivers[index])
        duplicate.identifier = self._make_unique_name(
            duplicate.identifier or "receiver",
            [item.identifier for item in project.model.receivers if item.identifier],
        )
        project.model.receivers.insert(index + 1, duplicate)
        self._after_mutation(project)
        return index + 1

    def delete_receiver(self, index: int) -> int | None:
        project = self.require_current_project()
        del project.model.receivers[index]
        self._after_mutation(project)
        if not project.model.receivers:
            return None
        return min(index, len(project.model.receivers) - 1)

    def add_geometry(self, kind: str = "box") -> int:
        project = self.require_current_project()
        existing = [item.label for item in project.model.geometry if item.label]
        geometry = default_geometry(project, len(project.model.geometry) + 1, kind=kind)
        geometry.label = self._make_unique_name(
            geometry.label or geometry.kind,
            existing,
        )
        project.model.geometry.append(geometry)
        self._after_mutation(project)
        return len(project.model.geometry) - 1

    def update_geometry(
        self,
        index: int,
        geometry: GeometryPrimitive,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.geometry[index] = geometry

        return self._mutate(mutate)

    def duplicate_geometry(self, index: int) -> int:
        project = self.require_current_project()
        duplicate = copy.deepcopy(project.model.geometry[index])
        duplicate.label = self._make_unique_name(
            duplicate.label or duplicate.kind,
            [item.label for item in project.model.geometry if item.label],
        )
        project.model.geometry.insert(index + 1, duplicate)
        self._after_mutation(project)
        return index + 1

    def delete_geometry(self, index: int) -> int | None:
        project = self.require_current_project()
        del project.model.geometry[index]
        self._after_mutation(project)
        if not project.model.geometry:
            return None
        return min(index, len(project.model.geometry) - 1)

    def add_geometry_import(self) -> int:
        project = self.require_current_project()
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
        self._after_mutation(project)
        return len(project.model.geometry_imports) - 1

    def update_geometry_import(
        self,
        index: int,
        geometry_import: GeometryImportDefinition,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.geometry_imports[index] = geometry_import

        return self._mutate(mutate)

    def duplicate_geometry_import(self, index: int) -> int:
        project = self.require_current_project()
        duplicate = copy.deepcopy(project.model.geometry_imports[index])
        duplicate.identifier = self._make_unique_name(
            duplicate.identifier or "geometry_import",
            [item.identifier for item in project.model.geometry_imports if item.identifier],
        )
        project.model.geometry_imports.insert(index + 1, duplicate)
        self._after_mutation(project)
        return index + 1

    def delete_geometry_import(self, index: int) -> int | None:
        project = self.require_current_project()
        del project.model.geometry_imports[index]
        self._after_mutation(project)
        if not project.model.geometry_imports:
            return None
        return min(index, len(project.model.geometry_imports) - 1)

    def add_antenna_model(self) -> int:
        project = self.require_current_project()
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
        self._after_mutation(project)
        return len(project.model.antenna_models) - 1

    def update_antenna_model(
        self,
        index: int,
        antenna_model: AntennaModelDefinition,
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.antenna_models[index] = antenna_model

        return self._mutate(mutate)

    def duplicate_antenna_model(self, index: int) -> int:
        project = self.require_current_project()
        duplicate = copy.deepcopy(project.model.antenna_models[index])
        duplicate.identifier = self._make_unique_name(
            duplicate.identifier or "antenna",
            [item.identifier for item in project.model.antenna_models if item.identifier],
        )
        project.model.antenna_models.insert(index + 1, duplicate)
        self._after_mutation(project)
        return index + 1

    def delete_antenna_model(self, index: int) -> int | None:
        project = self.require_current_project()
        del project.model.antenna_models[index]
        self._after_mutation(project)
        if not project.model.antenna_models:
            return None
        return min(index, len(project.model.antenna_models) - 1)

    def update_advanced_workspace(
        self,
        *,
        python_blocks: Sequence[str],
        raw_input_overrides: Sequence[str],
    ) -> ValidationResult:
        def mutate(project: Project) -> None:
            project.model.python_blocks = [item for item in python_blocks if item.strip()]
            project.advanced_input_overrides = [
                item for item in raw_input_overrides if item.strip()
            ]

        return self._mutate(mutate)

    def available_material_ids(self) -> list[str]:
        project = self.require_current_project()
        values = sorted(BUILTIN_MATERIAL_IDENTIFIERS) + [
            item.identifier for item in project.model.materials if item.identifier.strip()
        ]
        return list(dict.fromkeys(values))

    def available_waveform_ids(self) -> list[str]:
        project = self.require_current_project()
        return [item.identifier for item in project.model.waveforms if item.identifier.strip()]

    def _mutate(self, callback: Callable[[Project], None]) -> ValidationResult:
        project = self.require_current_project()
        callback(project)
        return self._after_mutation(project)

    def _after_mutation(self, project: Project) -> ValidationResult:
        validation = validate_project(project)
        self._state.current_project_validation = validation
        self._state.current_project_dirty = True
        return validation

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
