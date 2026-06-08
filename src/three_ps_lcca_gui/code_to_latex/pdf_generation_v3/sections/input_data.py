from __future__ import annotations

import re

from pylatex.utils import escape_latex

from ...bridge_data_latex import bridge_data_to_latex
from ..document import section, subsection


VEHICLES = [
    ("small_cars", "Small car"),
    ("big_cars", "Big car"),
    ("two_wheelers", "Two-wheeler"),
    ("o_buses", "Ordinary bus"),
    ("d_buses", "Deluxe bus"),
    ("lcv", "LCV - Light Commercial Vehicles"),
    ("hcv", "HCV - Two/Three Axle Heavy Commercial Vehicles"),
    ("mcv", "MCV - Multi Axle Vehicles"),
]

STRUCTURE_CHUNKS = [
    ("str_foundation", "Foundation", "Construction material quantities and rates for foundation"),
    ("str_sub_structure", "Substructure", "Construction material quantities and rates for substructure"),
    ("str_super_structure", "Superstructure", "Construction material quantities and rates for superstructure"),
    ("str_misc", "Miscellaneous", "Construction material quantities and rates for miscellaneous activities"),
]

EMDASH = r"\textemdash"


def _chunk(controller, name: str) -> dict:
    for method_name in ("get_fresh_chunk", "get_chunk"):
        method = getattr(controller, method_name, None)
        if callable(method):
            try:
                return method(name) or {}
            except Exception:
                pass
    try:
        from three_ps_lcca_gui.gui.components.utils.common_requested_data import get_chunk
        return get_chunk(name) or {}
    except Exception:
        return {}


def _fmt(value, decimals: int | None = None) -> str:
    if value in (None, ""):
        return EMDASH
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if decimals is not None:
        return f"{number:,.{decimals}f}"
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.2f}".rstrip("0").rstrip(".")


def _pct(value) -> str:
    return EMDASH if value in (None, "") else f"{_fmt(value)}%"


def _cell(value) -> str:
    if value in (None, ""):
        return EMDASH
    if value == EMDASH:
        return EMDASH
    return escape_latex(str(value))


def _header(headers: list[str]) -> str:
    return " & ".join(r"\textbf{" + escape_latex(h) + "}" for h in headers) + r" \\"


def _table(caption: str, label: str, headers: list[str], rows: list[list], col_spec: str) -> str:
    if not rows:
        rows = [[EMDASH for _ in headers]]
    body = [" & ".join(_cell(c) for c in row) + r" \\" for row in rows]
    head = _header(headers)
    return "\n".join([
        r"\begin{longtable}{" + col_spec + r"}",
        r"\caption{" + escape_latex(caption) + r"}\label{" + label + r"}\\",
        r"\toprule",
        head,
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        head,
        r"\midrule",
        r"\endhead",
        r"\midrule",
        r"\multicolumn{" + str(len(headers)) + r"}{r}{\footnotesize\textit{continued on next page}} \\",
        r"\endfoot",
        r"\bottomrule",
        r"\endlastfoot",
        *body,
        r"\end{longtable}",
    ])


def _rename_caption(latex: str, caption: str) -> str:
    if not latex:
        return ""
    latex = re.sub(r"\\caption\{[^{}]*\}", r"\\caption{" + escape_latex(caption) + "}", latex, count=1)
    latex = re.sub(r"\\caption\[[^\]]*\]\{[^{}]*\}", r"\\caption{" + escape_latex(caption) + "}", latex, count=1)
    return _keep_table_here(latex)


def _safe_export(fn, controller, caption: str) -> str:
    try:
        return _rename_caption(fn(controller) or "", caption)
    except Exception:
        return ""


def _keep_table_here(latex: str) -> str:
    return (
        latex
        .replace(r"\begin{table}[H]", r"\begin{table}[h!]")
        .replace(r"\begin{figure}[H]", r"\begin{figure}[h!]")
    )


def _structure_table(controller, chunk_id: str, caption: str) -> str:
    data = _chunk(controller, chunk_id)
    rows = []
    for component, items in data.items():
        for item in items or []:
            if item.get("state", {}).get("in_trash", False):
                continue
            values = item.get("values", {})
            rows.append([
                component,
                values.get("material_name", ""),
                _fmt(values.get("rate")),
                _fmt(values.get("quantity")),
                values.get("unit", ""),
                values.get("rate_source", ""),
            ])
    return _table(
        caption,
        "tab:" + chunk_id,
        ["Category", "Material", "Rate", "Quantity", "Unit", "Source"],
        rows,
        r"p{2.2cm}p{4.2cm}>{\raggedleft\arraybackslash}p{1.8cm}"
        r">{\raggedleft\arraybackslash}p{1.7cm}p{1.2cm}p{2.4cm}",
    )


def _financial_table(controller) -> str:
    data = _chunk(controller, "financial_data")
    rows = [
        ["Discount rate", _fmt(data.get("discount_rate"))],
        ["Inflation rate", _fmt(data.get("inflation_rate"))],
        ["Interest rate", _fmt(data.get("interest_rate"))],
        ["Investment ratio", _fmt(data.get("investment_ratio"))],
    ]
    return _table(
        "Financial inputs",
        "tab:financial_inputs",
        ["Description", "Value"],
        rows,
        r"p{9cm}>{\raggedleft\arraybackslash}p{4cm}",
    )


def _lcc_assumptions_table(controller) -> str:
    md = _chunk(controller, "maintenance_data")
    dem = _chunk(controller, "demolition_data")
    rows = [
        ["Routine inspection cost", _pct(md.get("routine_inspection_cost")), "Initial construction cost"],
        ["Major inspection cost", _pct(md.get("major_inspection_cost")), "Initial construction cost"],
        ["Replacement cost", _pct(md.get("bearing_exp_joint_cost")), "Initial superstructure cost"],
        ["Demolition and disposal cost", _pct(dem.get("demolition_cost_pct")), "Initial construction cost"],
    ]
    return _table(
        "Assumptions for different life cycle cost components",
        "tab:lcc_assumptions",
        ["", "Assumed percentage", ""],
        rows,
        r"p{6cm}>{\raggedleft\arraybackslash}p{3cm}p{5cm}",
    )


def _use_stage_details_table(controller) -> str:
    md = _chunk(controller, "maintenance_data")
    dem = _chunk(controller, "demolition_data")
    rows = [
        ["Duration of routine inspections (days)", ""],
        ["Interval for routine inspection (years)", _fmt(md.get("routine_inspection_freq"))],
        ["Duration of periodic maintenance (days)", ""],
        ["Interval for periodic maintenance (years)", _fmt(md.get("periodic_maintenance_freq"))],
        ["Duration of major inspection (days)", ""],
        ["Interval for major inspection (years)", _fmt(md.get("major_inspection_freq"))],
        ["Duration of replacement of bearing and expansion joint (days)", ""],
        ["Interval for replacement of bearing and expansion joint (years)", _fmt(md.get("bearing_exp_joint_freq"))],
        ["Duration of repairs and rehabilitation (days)", ""],
        ["Interval for repairs and rehabilitation (years)", _fmt(md.get("major_repair_freq"))],
        ["Duration of major repairs (days)", _fmt(md.get("major_repair_duration"))],
        ["Interval for major repairs (years)", _fmt(md.get("major_repair_freq"))],
        ["Duration of demolition and disposal (years)", _fmt(dem.get("demolition_duration"))],
    ]
    return _table(
        "Details related to duration and interval of use stage activities",
        "tab:use_stage_details",
        ["Description", "Value"],
        rows,
        r"p{10cm}>{\raggedleft\arraybackslash}p{4cm}",
    )


def _avg_traffic_table(controller) -> str:
    trd = _chunk(controller, "traffic_and_road_data")
    vehicle_data = trd.get("vehicle_data", {})
    rows = [[label, _fmt(vehicle_data.get(key, {}).get("vehicles_per_day"))] for key, label in VEHICLES]
    return _table(
        "Average Daily Traffic for each vehicle",
        "tab:avg_daily_traffic",
        ["Vehicle type", "Vehicles/day"],
        rows,
        r"p{9cm}>{\raggedleft\arraybackslash}p{4cm}",
    )


def _road_traffic_table(controller) -> str:
    trd = _chunk(controller, "traffic_and_road_data")
    bridge = _chunk(controller, "bridge_data")
    rows = [
        ["Average Daily Traffic (ADT)", ""],
        ["Average speed", ""],
        ["Additional travel time", _fmt(trd.get("additional_travel_time_min"))],
        ["Additional distance travelled, Average detour, Detour/affected distance", _fmt(trd.get("additional_reroute_distance_km"))],
        ["Terrain", ""],
        ["Alternate route's roadway classification", trd.get("alternate_road_carriageway", "")],
        ["One way or Two way", trd.get("vehicle_path_direction") or bridge.get("vehicle_path_direction", "")],
        ["Road capacity", _fmt(trd.get("hourly_capacity"))],
        ["Roughness, RG", _fmt(trd.get("road_roughness_mm_per_km"))],
        ["Rise/Fall, RF", _fmt(trd.get("road_rise_m_per_km"))],
        ["Rise, RS", ""],
        ["Fall, FL", ""],
        ["Crash rate", _fmt(trd.get("crash_rate_accidents_per_million_km"))],
        ["Work zone accident multiplier", _fmt(trd.get("work_zone_multiplier"))],
        ["No of peak hours", _fmt(trd.get("num_peak_hours"))],
    ]
    return _table(
        "Road and traffic related data",
        "tab:road_traffic_data",
        ["Description", "Value"],
        rows,
        r"p{10cm}>{\raggedleft\arraybackslash}p{4cm}",
    )


def _peak_hour_table(controller) -> str:
    trd = _chunk(controller, "traffic_and_road_data")
    dist = trd.get("peak_hour_distribution", {})
    count = int(trd.get("num_peak_hours") or len(dist) or 0)
    rows = []
    for i in range(1, count + 1):
        val = dist.get(f"peak_hour_{i}")
        rows.append([f"Peak Hour {i}", _fmt(float(val) * 100 if val is not None else None)])
    return _table(
        "Peak hour distribution",
        "tab:peak_hour_distribution",
        ["Hour Category", "Traffic proportion"],
        rows,
        r"p{8cm}>{\raggedleft\arraybackslash}p{5cm}",
    )


def _human_injury_table(controller) -> str:
    trd = _chunk(controller, "traffic_and_road_data")
    rows = [
        ["Fatal", _fmt(trd.get("severity_fatal"))],
        ["Major injury", _fmt(trd.get("severity_major"))],
        ["Minor injury", _fmt(trd.get("severity_minor"))],
    ]
    return _table(
        "Human injury cost data",
        "tab:human_injury_cost",
        ["Category of accident", "Accident distribution (%)"],
        rows,
        r"p{8cm}>{\raggedleft\arraybackslash}p{5cm}",
    )


def _vehicle_damage_table(controller) -> str:
    trd = _chunk(controller, "traffic_and_road_data")
    vehicle_data = trd.get("vehicle_data", {})
    rows = [[label, _fmt(vehicle_data.get(key, {}).get("accident_percentage"))] for key, label in VEHICLES]
    return _table(
        "Vehicle damage cost data",
        "tab:vehicle_damage_cost",
        ["Vehicle type", "Percentage of accidents for each vehicle type"],
        rows,
        r"p{8cm}>{\raggedleft\arraybackslash}p{5cm}",
    )


def _social_carbon_table(controller) -> str:
    result = _chunk(controller, "social_cost_data").get("result", {})
    rows = [["Social Cost of Carbon (SCC) Rs/kgCO2e", _fmt(result.get("cost_of_carbon_local"), 4)]]
    return _table(
        "Social Cost of Carbon",
        "tab:social_cost_carbon",
        ["Description", "Value"],
        rows,
        r"p{9cm}>{\raggedleft\arraybackslash}p{4cm}",
    )


def _material_emission_table(controller) -> str:
    rows = []
    seen = set()
    for chunk_id, category, _caption in STRUCTURE_CHUNKS:
        for _component, items in _chunk(controller, chunk_id).items():
            for item in items or []:
                if item.get("state", {}).get("in_trash", False):
                    continue
                if item.get("state", {}).get("included_in_carbon_emission") is not True:
                    continue
                values = item.get("values", {})
                material = values.get("material_name", "")
                if not material or material in seen:
                    continue
                seen.add(material)
                rows.append([
                    category,
                    material,
                    _fmt(values.get("quantity")),
                    values.get("unit", ""),
                    _fmt(values.get("conversion_factor"), 2),
                    _fmt(values.get("carbon_emission"), 4),
                    values.get("carbon_unit", ""),
                ])
    return _table(
        "Material related factors for emission",
        "tab:material_emission_factors",
        ["Category", "Material", "Quantity", "Unit", "Conversion factor", "Emission factor", "Emission factor unit"],
        rows,
        r"p{1.8cm}p{3.4cm}>{\raggedleft\arraybackslash}p{1.4cm}p{1cm}"
        r">{\raggedleft\arraybackslash}p{1.8cm}>{\raggedleft\arraybackslash}p{1.7cm}p{2.1cm}",
    )


def _use_stage_emissions_table(controller) -> str:
    md = _chunk(controller, "maintenance_data")
    dem = _chunk(controller, "demolition_data")
    rows = [
        ["Periodic maintenance carbon emission", _pct(md.get("periodic_maintenance_carbon_cost"))],
        ["Major repair related carbon emission", _pct(md.get("major_repair_carbon_cost"))],
        ["Demolition and disposal related carbon emissions", _pct(dem.get("demolition_carbon_cost_pct"))],
    ]
    return _table(
        "Assumptions for use stage and end of life emissions",
        "tab:use_stage_emission_assumptions",
        ["", "Assumed % of initial emission"],
        rows,
        r"p{9cm}>{\raggedleft\arraybackslash}p{4cm}",
    )


def _vehicle_emission_factors_table(controller) -> str:
    div = _chunk(controller, "diversion_emissions")
    if not div:
        div = _chunk(controller, "traffic_and_road_data").get("diversion_emissions", {})
    factors = div.get("emission_factors", {})
    rows = [[label, _fmt(factors.get(key), 4)] for key, label in VEHICLES]
    return _table(
        "Vehicle related emission factors",
        "tab:vehicle_emission_factors",
        ["Vehicle type", "Emission factor"],
        rows,
        r"p{9cm}>{\raggedleft\arraybackslash}p{4cm}",
    )


def _material_index(controller) -> dict:
    index = {}
    for chunk_id, category, _caption in STRUCTURE_CHUNKS:
        for component, items in _chunk(controller, chunk_id).items():
            for item in items or []:
                mat_id = item.get("id")
                if mat_id:
                    index[mat_id] = (category, component, item)
    return index


def _transport_table(controller) -> str:
    data = _chunk(controller, "transport_data")
    index = _material_index(controller)
    rows = []
    for entry in data.get("vehicles", []):
        if entry.get("state", {}).get("in_trash", False):
            continue
        vehicle = entry.get("vehicle", {})
        route = entry.get("route", {})
        for mat in entry.get("materials", []) or [{}]:
            mat_id = mat.get("uuid") if isinstance(mat, dict) else mat
            record = index.get(mat_id)
            material = record[2].get("values", {}).get("material_name", "") if record else ""
            rows.append([
                material,
                vehicle.get("name", ""),
                _fmt(vehicle.get("gross_weight"), 2),
                _fmt(vehicle.get("capacity"), 2),
                _fmt(route.get("distance_km"), 2),
                route.get("origin", ""),
                route.get("destination", ""),
                _fmt(vehicle.get("emission_factor"), 4),
            ])
    return _table(
        "Data for emissions related to transportation of material",
        "tab:transport_emission_data",
        ["Transport Material", "Vehicle name", "GVW (tonne)", "Cargo capacity (tonne)", "Distance travelled (km)", "Source", "Destination", "Emission Factor (kgCO2e/tonne-km)"],
        rows,
        r"p{2.5cm}p{1.7cm}>{\raggedleft\arraybackslash}p{1.2cm}"
        r">{\raggedleft\arraybackslash}p{1.4cm}>{\raggedleft\arraybackslash}p{1.4cm}"
        r"p{1.6cm}p{1.6cm}>{\raggedleft\arraybackslash}p{1.8cm}",
    )


def _onsite_emissions_table(controller) -> str:
    data = _chunk(controller, "machinery_emissions_data")
    rows = []
    if data.get("mode") == "lumpsum":
        ls = data.get("lumpsum", {})
        rows = [
            ["Electricity", "Electricity", _fmt(ls.get("elec_consumption_per_day"), 2), "", _fmt(ls.get("elec_days")), _fmt(ls.get("elec_ef"), 4)],
            ["Fuel", "Fuel", _fmt(ls.get("fuel_consumption_per_day"), 2), "", _fmt(ls.get("fuel_days")), _fmt(ls.get("fuel_ef"), 4)],
        ]
    else:
        for row in data.get("detailed", {}).get("rows", []):
            rows.append([
                row.get("name", ""),
                row.get("source", ""),
                _fmt(row.get("rate"), 2),
                _fmt(row.get("hrs"), 2),
                _fmt(row.get("days")),
                _fmt(row.get("ef"), 4),
            ])
    return _table(
        "Emissions from on-site activities during construction",
        "tab:onsite_emissions",
        ["Construction Equipment", "Energy Source", "Diesel consumption (l/hour) or Electricity (Kw)", "Avg number of hours used per day", "Number of days the equipment would be used", "Emission factor (kgCO2e/unit)"],
        rows,
        r"p{2.9cm}p{2cm}>{\raggedleft\arraybackslash}p{2.4cm}"
        r">{\raggedleft\arraybackslash}p{2cm}>{\raggedleft\arraybackslash}p{2cm}"
        r">{\raggedleft\arraybackslash}p{2cm}",
    )


def input_data_to_latex(controller=None) -> str:
    parts = [
        section("Input data"),
        subsection("Bridge geometry and description"),
        _safe_export(bridge_data_to_latex, controller, "Bridge description"),
        subsection("Financial inputs"),
        _financial_table(controller),
        subsection("Construction data"),
    ]
    for chunk_id, _category, caption in STRUCTURE_CHUNKS:
        parts.append(_structure_table(controller, chunk_id, caption))
    parts.extend([
        _lcc_assumptions_table(controller),
        _use_stage_details_table(controller),
        subsection("Traffic data"),
        _avg_traffic_table(controller),
        _road_traffic_table(controller),
        _peak_hour_table(controller),
        _human_injury_table(controller),
        _vehicle_damage_table(controller),
        subsection("Environmental input data"),
        _social_carbon_table(controller),
        _material_emission_table(controller),
        _use_stage_emissions_table(controller),
        _vehicle_emission_factors_table(controller),
        _transport_table(controller),
        _onsite_emissions_table(controller),
    ])
    return "\n\n".join(part for part in parts if part and part.strip())
