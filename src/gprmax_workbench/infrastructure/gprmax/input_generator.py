from __future__ import annotations

from dataclasses import dataclass, field

from ...domain.execution_status import SimulationMode
from ...domain.gprmax_config import SimulationRunConfig
from ...domain.models import (
    AntennaModelDefinition,
    GeometryImportDefinition,
    GeometryPrimitive,
    GeometryView,
    MaterialDefinition,
    Project,
    ReceiverDefinition,
    SourceDefinition,
    Vector3,
    WaveformDefinition,
)


class InputGenerationError(ValueError):
    """Raised when the current project cannot be rendered to gprMax input."""


@dataclass(slots=True)
class GeneratedInput:
    text: str
    warnings: list[str] = field(default_factory=list)


class GprMaxInputGenerator:
    """Converts the project model into a gprMax input-file representation."""

    _default_receiver_outputs = ("Ex", "Ey", "Ez", "Hx", "Hy", "Hz")

    def generate(
        self,
        project: Project,
        configuration: SimulationRunConfig,
        *,
        output_dir: str,
    ) -> GeneratedInput:
        warnings: list[str] = []
        lines: list[str] = [
            f"#title: {project.model.title or project.metadata.name}",
            "#messages: y",
            f"#domain: {self._format_vector(project.model.domain.size_m)}",
            f"#dx_dy_dz: {self._format_vector(project.model.domain.resolution_m)}",
            f"#time_window: {self._format_number(project.model.domain.time_window_s)}",
            (
                "#pml_cells: "
                f"{project.model.domain.pml_cells.x_min} "
                f"{project.model.domain.pml_cells.y_min} "
                f"{project.model.domain.pml_cells.z_min} "
                f"{project.model.domain.pml_cells.x_max} "
                f"{project.model.domain.pml_cells.y_max} "
                f"{project.model.domain.pml_cells.z_max}"
            ),
            f"#output_dir: {output_dir}",
        ]

        lines.extend(self._render_material(item) for item in project.model.materials)
        lines.extend(self._render_waveform(item) for item in project.model.waveforms)
        lines.extend(self._render_source(item) for item in project.model.sources)
        for item in project.model.receivers:
            lines.append(self._render_receiver(item))
        lines.extend(self._render_geometry(item) for item in project.model.geometry)
        lines.extend(
            self._render_geometry_import(item)
            for item in project.model.geometry_imports
        )
        for item in project.model.antenna_models:
            lines.extend(self._render_antenna_model(item))
        lines.extend(self._render_geometry_view(item) for item in project.model.geometry_views)

        if configuration.mode == SimulationMode.GEOMETRY_ONLY and not project.model.geometry_views:
            warnings.append(
                "Geometry-only mode is enabled but no geometry views are defined. gprMax will still process geometry without image outputs."
            )

        if not project.model.waveforms:
            warnings.append("No waveforms are defined in the project.")
        if not project.model.sources:
            warnings.append("No sources are defined in the project.")
        if not project.model.receivers:
            warnings.append("No receivers are defined in the project.")

        for block in project.model.python_blocks:
            stripped = block.strip("\n")
            if not stripped:
                continue
            lines.append("#python:")
            lines.extend(stripped.splitlines())
            lines.append("#end_python:")

        lines.extend(
            line.rstrip()
            for line in project.advanced_input_overrides
            if line.strip()
        )

        return GeneratedInput(text="\n".join(lines).strip() + "\n", warnings=warnings)

    def _render_material(self, material: MaterialDefinition) -> str:
        return (
            "#material: "
            f"{self._format_number(material.relative_permittivity)} "
            f"{self._format_number(material.conductivity)} "
            f"{self._format_number(material.relative_permeability)} "
            f"{self._format_number(material.magnetic_loss)} "
            f"{material.identifier}"
        )

    def _render_waveform(self, waveform: WaveformDefinition) -> str:
        return (
            "#waveform: "
            f"{waveform.kind} "
            f"{self._format_number(waveform.amplitude)} "
            f"{self._format_number(waveform.center_frequency_hz)} "
            f"{waveform.identifier}"
        )

    def _render_source(self, source: SourceDefinition) -> str:
        source_renderers = {
            "hertzian_dipole": self._render_hertzian_dipole,
            "magnetic_dipole": self._render_hertzian_dipole,
            "voltage_source": self._render_voltage_source,
        }
        renderer = source_renderers.get(source.kind)
        if renderer is None:
            raise InputGenerationError(
                f"Unsupported source kind '{source.kind}'."
            )
        return renderer(source)

    def _render_hertzian_dipole(self, source: SourceDefinition) -> str:
        line = (
            f"#{source.kind}: "
            f"{source.axis} "
            f"{self._format_vector(source.position_m)} "
            f"{source.waveform_id}"
        )
        if source.delay_s > 0:
            line = f"{line} {self._format_number(source.delay_s)}"
        return line

    def _render_voltage_source(self, source: SourceDefinition) -> str:
        resistance = source.resistance_ohms
        if resistance is None:
            resistance = float(source.parameters.get("resistance_ohms", 50))
        line = (
            "#voltage_source: "
            f"{source.axis} "
            f"{self._format_vector(source.position_m)} "
            f"{self._format_number(float(resistance))} "
            f"{source.waveform_id}"
        )
        if source.delay_s > 0:
            line = f"{line} {self._format_number(source.delay_s)}"
        return line

    def _render_receiver(self, receiver: ReceiverDefinition) -> str:
        outputs = list(receiver.outputs)
        identifier = receiver.identifier.strip()

        if identifier and not outputs:
            outputs = list(self._default_receiver_outputs)
        if outputs and not identifier:
            identifier = "rx"

        if identifier and outputs:
            return (
                "#rx: "
                f"{self._format_vector(receiver.position_m)} "
                f"{identifier} "
                f"{' '.join(outputs)}"
            )
        return f"#rx: {self._format_vector(receiver.position_m)}"

    def _render_geometry(self, geometry: GeometryPrimitive) -> str:
        geometry_renderers = {
            "box": self._render_box,
            "sphere": self._render_sphere,
            "cylinder": self._render_cylinder,
        }
        renderer = geometry_renderers.get(geometry.kind)
        if renderer is None:
            raise InputGenerationError(
                f"Unsupported geometry primitive '{geometry.kind}'."
            )
        return renderer(geometry)

    def _render_box(self, geometry: GeometryPrimitive) -> str:
        line = (
            "#box: "
            f"{self._format_from_parameters(geometry, 'lower_left_m')} "
            f"{self._format_from_parameters(geometry, 'upper_right_m')} "
            f"{self._require_material_id(geometry)}"
        )
        return self._append_dielectric_smoothing(line, geometry)

    def _render_sphere(self, geometry: GeometryPrimitive) -> str:
        center = self._format_from_parameters(geometry, "center_m")
        radius = self._format_number(float(geometry.parameters["radius_m"]))
        line = f"#sphere: {center} {radius} {self._require_material_id(geometry)}"
        return self._append_dielectric_smoothing(line, geometry)

    def _render_cylinder(self, geometry: GeometryPrimitive) -> str:
        line = (
            "#cylinder: "
            f"{self._format_from_parameters(geometry, 'start_m')} "
            f"{self._format_from_parameters(geometry, 'end_m')} "
            f"{self._format_number(float(geometry.parameters['radius_m']))} "
            f"{self._require_material_id(geometry)}"
        )
        return self._append_dielectric_smoothing(line, geometry)

    def _render_geometry_view(self, view: GeometryView) -> str:
        return (
            "#geometry_view: "
            f"{self._format_vector(view.lower_left_m)} "
            f"{self._format_vector(view.upper_right_m)} "
            f"{self._format_vector(view.resolution_m)} "
            f"{view.filename} {view.mode}"
        )

    def _render_geometry_import(self, geometry_import: GeometryImportDefinition) -> str:
        line = (
            "#geometry_objects_read: "
            f"{self._format_vector(geometry_import.position_m)} "
            f"{geometry_import.geometry_hdf5} "
            f"{geometry_import.materials_file}"
        )
        if geometry_import.dielectric_smoothing:
            line = f"{line} y"
        return line

    def _render_antenna_model(self, antenna: AntennaModelDefinition) -> list[str]:
        rotation = ", rotate90=True" if antenna.rotate90 else ""
        invocation = (
            f"{antenna.function_name}("
            f"{self._format_number(antenna.position_m.x)}, "
            f"{self._format_number(antenna.position_m.y)}, "
            f"{self._format_number(antenna.position_m.z)}, "
            f"resolution={self._format_number(antenna.resolution_m)}"
            f"{rotation})"
        )
        return [
            "#python:",
            f"from {antenna.module_path} import {antenna.function_name}",
            invocation,
            "#end_python:",
        ]

    def _format_from_parameters(self, geometry: GeometryPrimitive, key: str) -> str:
        raw = geometry.parameters.get(key)
        if not isinstance(raw, dict):
            raise InputGenerationError(
                f"Geometry '{geometry.kind}' is missing the '{key}' vector parameter."
            )
        return self._format_vector(
            Vector3(
                x=float(raw["x"]),
                y=float(raw["y"]),
                z=float(raw["z"]),
            )
        )

    def _require_material_id(self, geometry: GeometryPrimitive) -> str:
        if not geometry.material_ids:
            raise InputGenerationError(
                f"Geometry '{geometry.kind}' does not reference a material."
            )
        return geometry.material_ids[0]

    def _append_dielectric_smoothing(
        self,
        line: str,
        geometry: GeometryPrimitive,
    ) -> str:
        smoothing = "y" if geometry.dielectric_smoothing else "n"
        return f"{line} {smoothing}"

    def _format_vector(self, vector: Vector3) -> str:
        return " ".join(
            self._format_number(value) for value in (vector.x, vector.y, vector.z)
        )

    def _format_number(self, value: float) -> str:
        return f"{value:.12g}"
