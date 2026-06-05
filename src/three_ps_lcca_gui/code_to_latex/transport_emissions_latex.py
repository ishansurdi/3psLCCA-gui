import math
import pandas as pd
from ..gui.components.utils.common_requested_data import get_chunk, get_transport_data
from ..gui.components.utils.definitions import STRUCTURE_CHUNKS, UNIT_DIMENSION, UNIT_DISPLAY
from .SETTINGS import DECIMAL_PLACES_FOR_LATEX

_FMT    = f"{{:.{DECIMAL_PLACES_FOR_LATEX}f}}"
_EMDASH = r"\textemdash"


def _build_material_index() -> dict:
    index = {}
    for chunk_id, category in STRUCTURE_CHUNKS:
        for component, items in get_chunk(chunk_id).items():
            for item in items:
                mat_id = item.get("id")
                if mat_id:
                    index[mat_id] = {"item": item, "category": category, "component": component}
    return index


def _material_entry_values(mat_entry):
    if isinstance(mat_entry, dict):
        return mat_entry.get("uuid"), float(mat_entry.get("kg_factor", 1.0) or 0)
    return mat_entry, 1.0


def _vehicle_table_to_latex(entry: dict, mat_index: dict, table_no: int) -> str:
    vehicle  = entry.get("vehicle", {})
    route    = entry.get("route", {})

    capacity     = float(vehicle.get("capacity",      0) or 0)
    gross_weight = float(vehicle.get("gross_weight",  0) or 0)
    empty_weight = float(vehicle.get("empty_weight",  max(0.0, gross_weight - capacity)) or 0)
    distance     = float(route.get("distance_km",     0) or 0)
    ef           = float(vehicle.get("emission_factor", 0) or 0)

    rows = []
    total_emission = 0.0

    for mat_entry in entry.get("materials", []):
        mat_uuid, kg_factor = _material_entry_values(mat_entry)

        if mat_uuid not in mat_index:
            rows.append({"Material": "Unknown", "Category": "",
                         "kg Conversion Factor": None,
                         "Quantity (kg)": None, "Trips": None,
                         "Emissions (kgCO₂e)": 0.0, "Notes": "Material removed from structure"})
            continue

        record = mat_index[mat_uuid]
        item   = record["item"]

        if item.get("state", {}).get("in_trash", False):
            v = item.get("values", {})
            rows.append({"Material": v.get("material_name", ""), "Category": record["category"],
                         "kg Conversion Factor": None, "Quantity (kg)": None, "Trips": None,
                         "Emissions (kgCO₂e)": 0.0, "Notes": "In trash"})
            continue

        v        = item.get("values", {})
        unit     = v.get("unit", "")
        quantity = float(v.get("quantity", 0) or 0)
        qty_kg   = quantity * kg_factor
        qty_t    = qty_kg / 1000.0
        trips    = math.ceil(qty_t / capacity) if capacity > 0 else 0
        emission = (gross_weight + empty_weight) * trips * distance * ef
        total_emission += emission

        notes = []
        if quantity <= 0:
            notes.append("Zero quantity")
        if qty_kg <= 0 < quantity:
            notes.append("Zero kg — check factor")
        if trips > 1000:
            notes.append(f"{trips} trips — unusually high")
        if UNIT_DIMENSION.get(str(unit).lower()) != "Mass" and abs(kg_factor - 1.0) < 1e-6:
            notes.append(f"1:1 factor for {UNIT_DISPLAY.get(unit, unit)} — verify")

        rows.append({
            "Material":              v.get("material_name", ""),
            "Category":              record["category"],
            "kg Conversion Factor":  kg_factor,
            "Quantity (kg)":         qty_kg,
            "Trips":                 float(trips),
            "Emissions (kgCO₂e)":  emission,
            "Notes":                 " | ".join(notes),
        })

    df = pd.DataFrame(rows)
    vehicle_name = vehicle.get("name", "Vehicle") or "Vehicle"
    caption = (
        f"{vehicle_name} — {distance:.{DECIMAL_PLACES_FOR_LATEX}f}\\,km — "
        f"{total_emission:,.{DECIMAL_PLACES_FOR_LATEX}f}\\,kgCO\\textsubscript{{2}}e; "
        f"Capacity {capacity:.{DECIMAL_PLACES_FOR_LATEX}f}\\,t, "
        f"Gross {gross_weight:.{DECIMAL_PLACES_FOR_LATEX}f}\\,t, "
        f"Emission Factor {ef:.{DECIMAL_PLACES_FOR_LATEX}f}\\,kgCO\\textsubscript{{2}}e/t\\,km"
    )

    return (
        df.style.hide(axis="index")
        .format(_FMT, subset=["kg Conversion Factor", "Quantity (kg)", "Trips", "Emissions (kgCO₂e)"],
                na_rep=_EMDASH)
        .to_latex(
            caption=caption,
            label=f"tab:transport_emissions_{table_no}",
            hrules=True,
            column_format="p{3.5cm}p{2cm}rrrrp{3cm}",
            environment="longtable",
        )
    ) or ""


def transport_emissions_to_latex(controller=None) -> str:
    data      = get_transport_data()
    mat_index = _build_material_index()

    tables   = []
    table_no = 1

    for entry in data.get("vehicles", []):
        if entry.get("state", {}).get("in_trash", False):
            continue
        tables.append(_vehicle_table_to_latex(entry, mat_index, table_no))
        table_no += 1

    return "\n\n".join(t for t in tables if t)
