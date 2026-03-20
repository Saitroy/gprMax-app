from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GprMaxCommandTemplate:
    key: str
    category: str
    title: str
    template: str
    description: str


class GprMaxCommandRegistry:
    """Provides grouped command templates for the advanced input workspace."""

    def __init__(self) -> None:
        self._templates = tuple(_COMMAND_TEMPLATES)

    def categories(self) -> list[str]:
        return sorted({item.category for item in self._templates})

    def templates(self, category: str | None = None) -> list[GprMaxCommandTemplate]:
        if category is None or category == "all":
            return list(self._templates)
        return [item for item in self._templates if item.category == category]

    def get(self, key: str) -> GprMaxCommandTemplate | None:
        for item in self._templates:
            if item.key == key:
                return item
        return None


_COMMAND_TEMPLATES: list[GprMaxCommandTemplate] = [
    GprMaxCommandTemplate("title", "general", "#title", "#title: Example model", "Sets the model title."),
    GprMaxCommandTemplate("messages", "general", "#messages", "#messages: y", "Controls runtime console messages."),
    GprMaxCommandTemplate("domain", "general", "#domain", "#domain: 1.0 1.0 0.2", "Defines the domain size in metres."),
    GprMaxCommandTemplate("dx_dy_dz", "general", "#dx_dy_dz", "#dx_dy_dz: 0.002 0.002 0.002", "Defines the spatial discretisation."),
    GprMaxCommandTemplate("time_window", "general", "#time_window", "#time_window: 6e-9", "Defines the simulation time window in seconds."),
    GprMaxCommandTemplate("material", "materials", "#material", "#material: 6.0 0.001 1.0 0.0 soil", "Adds a standard material definition."),
    GprMaxCommandTemplate("soil_peplinski", "materials", "#soil_peplinski", "#soil_peplinski: 0.5 0.5 0.001 0.3 0.7 sand_mix", "Adds a Peplinski soil material model."),
    GprMaxCommandTemplate("debye", "materials", "#add_dispersion_debye", "#add_dispersion_debye: 2 7.0 0.05 1e-11 4.0 0.01 8e-11 water_like", "Adds Debye dispersion parameters to a material."),
    GprMaxCommandTemplate("lorentz", "materials", "#add_dispersion_lorentz", "#add_dispersion_lorentz: 1 2.0 1e9 5e7 resonant_mat", "Adds Lorentz dispersion parameters."),
    GprMaxCommandTemplate("drude", "materials", "#add_dispersion_drude", "#add_dispersion_drude: 1 1e16 2e13 conductive_mat", "Adds Drude dispersion parameters."),
    GprMaxCommandTemplate("box", "objects", "#box", "#box: 0.1 0.1 0.0 0.4 0.3 0.15 soil y", "Adds a box primitive."),
    GprMaxCommandTemplate("sphere", "objects", "#sphere", "#sphere: 0.35 0.2 0.08 0.05 soil y", "Adds a sphere primitive."),
    GprMaxCommandTemplate("cylinder", "objects", "#cylinder", "#cylinder: 0.2 0.2 0.0 0.2 0.2 0.15 0.04 soil y", "Adds a cylinder primitive."),
    GprMaxCommandTemplate("triangle", "objects", "#triangle", "#triangle: 0.1 0.1 0.0 0.2 0.1 0.0 0.15 0.2 0.0 soil y", "Adds a triangle primitive."),
    GprMaxCommandTemplate("plate", "objects", "#plate", "#plate: 0.1 0.1 0.05 0.4 0.1 0.05 pec", "Adds a PEC plate."),
    GprMaxCommandTemplate("edge", "objects", "#edge", "#edge: 0.1 0.1 0.05 0.4 0.1 0.05 pec", "Adds a PEC edge."),
    GprMaxCommandTemplate("fractal_box", "objects", "#fractal_box", "#fractal_box: 0.1 0.1 0.0 0.4 0.4 0.15 3 1 0.4 0.6 soil", "Adds a fractal box volume."),
    GprMaxCommandTemplate("geometry_read", "imports", "#geometry_objects_read", "#geometry_objects_read: 0.0 0.0 0.0 assets/object.h5 assets/materials.txt y", "Imports geometry objects from HDF5 plus materials text."),
    GprMaxCommandTemplate("geometry_write", "imports", "#geometry_objects_write", "#geometry_objects_write: 0.0 0.0 0.0 0.5 0.5 0.2 cache/exported_geometry", "Exports generated geometry for reuse."),
    GprMaxCommandTemplate("waveform", "sources", "#waveform", "#waveform: ricker 1.0 1.5e9 wf1", "Defines a waveform."),
    GprMaxCommandTemplate("hertzian", "sources", "#hertzian_dipole", "#hertzian_dipole: z 0.2 0.2 0.02 wf1", "Adds a Hertzian dipole source."),
    GprMaxCommandTemplate("magnetic", "sources", "#magnetic_dipole", "#magnetic_dipole: z 0.2 0.2 0.02 wf1", "Adds a magnetic dipole source."),
    GprMaxCommandTemplate("voltage", "sources", "#voltage_source", "#voltage_source: z 0.2 0.2 0.02 50 wf1", "Adds a voltage source."),
    GprMaxCommandTemplate("transmission_line", "sources", "#transmission_line", "#transmission_line: z 0.2 0.2 0.02 50 wf1", "Adds a transmission line source."),
    GprMaxCommandTemplate("rx", "outputs", "#rx", "#rx: 0.25 0.2 0.02 rx1 Ex Ey Ez Hx Hy Hz", "Adds a single receiver."),
    GprMaxCommandTemplate("rx_array", "outputs", "#rx_array", "#rx_array: 0.1 0.2 0.02 0.5 0.2 0.02 0.01 0 0", "Adds a receiver array."),
    GprMaxCommandTemplate("src_steps", "outputs", "#src_steps", "#src_steps: 0.005 0 0", "Moves sources between model runs for profile generation."),
    GprMaxCommandTemplate("rx_steps", "outputs", "#rx_steps", "#rx_steps: 0.005 0 0", "Moves receivers between model runs for profile generation."),
    GprMaxCommandTemplate("geometry_view", "outputs", "#geometry_view", "#geometry_view: 0 0 0 1.0 1.0 0.2 0.002 0.002 0.002 geometry n", "Outputs a geometry snapshot."),
    GprMaxCommandTemplate("snapshot", "outputs", "#snapshot", "#snapshot: 0 0 0 1.0 1.0 0.2 0.002 0.002 0.002 3e-9 snapshot", "Outputs a field snapshot."),
    GprMaxCommandTemplate("pml_cells", "pml", "#pml_cells", "#pml_cells: 10 10 10 10 10 10", "Defines PML thickness in cells."),
    GprMaxCommandTemplate("pml_formulation", "pml", "#pml_formulation", "#pml_formulation: horipml", "Selects the PML formulation."),
    GprMaxCommandTemplate("pml_cfs", "pml", "#pml_cfs", "#pml_cfs: forward 2 0.0 1.0 0.0 1.0", "Adds advanced PML scaling parameters."),
]
