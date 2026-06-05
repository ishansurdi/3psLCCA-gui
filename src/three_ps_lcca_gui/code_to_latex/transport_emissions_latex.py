import math

import pandas as pd

from ..gui.project_controller import ProjectController
# from ..gui.components.utils.definitions import STRUCTURE_CHUNKS, UNIT_DIMENSION
from ..gui.components.utils.definitions import UNIT_DIMENSION
from .chunks import TRANSPORT_DATA_CHUNK, STRUCTURE_MATERIAL_CHUNKS

CHUNK = TRANSPORT_DATA_CHUNK


def _fmt_number(value, decimals=2) -> str:
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "--"


def _fmt_int(value) -> str:
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "--"


def _build_material_index(controller: ProjectController) -> dict:
    index = {}

    for chunk_id, category in STRUCTURE_MATERIAL_CHUNKS:
        data = controller.engine.fetch_chunk(chunk_id) or {}

        for component, items in data.items():
            for item in items:
                material_id = item.get("id")
                if material_id:
                    index[material_id] = {
                        "item": item,
                        "category": category,
                        "component": component,
                    }

    return index


def _material_entry_values(mat_entry):
    if isinstance(mat_entry, dict):
        return mat_entry.get("uuid"), float(mat_entry.get("kg_factor", 1.0) or 0)
    return mat_entry, 1.0


def _warning_text(quantity, qty_kg, trips, unit, kg_factor) -> str:
    warnings = []
    if quantity <= 0:
        warnings.append("Zero quantity")
    if qty_kg <= 0 and quantity > 0:
        warnings.append("Zero kg - check factor")
    if trips > 1000:
        warnings.append(f"{trips} trips - unusually high")
    if UNIT_DIMENSION.get(str(unit).lower()) != "Mass" and abs(kg_factor - 1.0) < 1e-6:
        warnings.append(f"1:1 factor for {unit} - verify conversion")
    return " | ".join(warnings)


def _vehicle_table_to_latex(entry, mat_index: dict, table_no: int) -> str:
    vehicle = entry.get("vehicle", {})
    route = entry.get("route", {})

    capacity = float(vehicle.get("capacity", 0) or 0)
    gross_weight = float(vehicle.get("gross_weight", 0) or 0)
    empty_weight = float(vehicle.get("empty_weight", max(0.0, gross_weight - capacity)) or 0)
    distance = float(route.get("distance_km", 0) or 0)
    emission_factor = float(vehicle.get("emission_factor", 0) or 0)

    rows = []
    total_emission = 0.0

    for mat_entry in entry.get("materials", []):
        mat_uuid, kg_factor = _material_entry_values(mat_entry)

        if mat_uuid not in mat_index:
            rows.append(["Unknown", "", "--", "--", "--", "0.00", "Material removed from structure"])
            continue

        record = mat_index[mat_uuid]
        item = record["item"]

        if item.get("state", {}).get("in_trash", False):
            values = item.get("values", {})
            rows.append([
                values.get("material_name", ""),
                record["category"],
                "--",
                "--",
                "--",
                "0.00",
                "In trash",
            ])
            continue

        values = item.get("values", {})
        quantity = float(values.get("quantity", 0) or 0)
        unit = values.get("unit", "")
        qty_kg = quantity * kg_factor
        qty_tonne = qty_kg / 1000.0
        trips = math.ceil(qty_tonne / capacity) if capacity > 0 else 0
        emission = (gross_weight + empty_weight) * trips * distance * emission_factor
        total_emission += emission

        rows.append([
            values.get("material_name", ""),
            record["category"],
            _fmt_number(kg_factor),
            _fmt_int(qty_kg),
            str(trips),
            _fmt_number(emission),
            _warning_text(quantity, qty_kg, trips, unit, kg_factor),
        ])

    df = pd.DataFrame(
        rows,
        columns=[
            "Material",
            "Category",
            "kg Factor",
            "Quantity kg",
            "Trips",
            "Emission kgCO2e",
            "Warnings",
        ],
    )

    vehicle_name = vehicle.get("name", "Vehicle") or "Vehicle"
    caption = (
        f"{vehicle_name} - {distance:.2f} km - {total_emission:,.2f} kgCO2e; "
        f"Capacity {capacity:.2f}t, Gross Wt {gross_weight:.2f}t, "
        f"Empty Wt {empty_weight:.2f}t, EF {emission_factor:.2f} kgCO2e/t-km"
    )

    return df.to_latex(
        index=False,
        caption=caption,
        label=f"tab:transport_emissions_{table_no}",
        escape=True,
        longtable=True,
    )


def transport_emissions_to_latex(controller: ProjectController) -> str:
    data = controller.engine.fetch_chunk(CHUNK) or {}
    vehicles = data.get("vehicles", [])
    mat_index = _build_material_index(controller)

    tables = []
    table_no = 1

    for entry in vehicles:
        if entry.get("state", {}).get("in_trash", False):
            continue

        tables.append(_vehicle_table_to_latex(entry, mat_index, table_no))
        table_no += 1

    return "\n\n".join(tables)
