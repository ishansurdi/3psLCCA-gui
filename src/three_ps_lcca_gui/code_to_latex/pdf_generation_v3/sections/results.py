from __future__ import annotations

import re

from ...results_latex import results_to_latex
from ..document import paragraph, placeholder_figure, section, subsection, subsubsection
from .input_data import EMDASH, STRUCTURE_CHUNKS, _chunk, _fmt, _keep_table_here, _table


PILLARS = [
    ("economic", "Economic"),
    ("environmental", "Environmental"),
    ("social", "Social"),
]

STAGES = [
    ("initial_stage", "Initial stage"),
    ("use_stage", "Use stage"),
    ("reconstruction", "Reconstruction"),
    ("end_of_life", "End of life"),
]

CREDIT_KEYS = {"total_scrap_value"}


def _cache(controller) -> dict:
    calculated = _calculated_cache(controller)
    if calculated.get("results"):
        return calculated

    cache = _chunk(controller, "comparison_cache")
    if isinstance(cache, dict) and cache.get("results"):
        return cache
    return {}


def _results(cache: dict) -> dict:
    return cache.get("results", {}) or {}


def _currency(cache: dict, controller) -> str:
    return cache.get("currency") or _chunk(controller, "general_info").get("project_currency", "")


def _as_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _construction_work_data(controller) -> dict:
    existing = _chunk(controller, "construction_work_data")
    if existing:
        return existing

    page_names = {
        "str_foundation": "Foundation",
        "str_sub_structure": "Sub-Structure",
        "str_super_structure": "Super-Structure",
        "str_misc": "Miscellaneous",
    }
    pages_data = {}
    grand_total = 0.0
    for chunk_id, page_name, _caption in STRUCTURE_CHUNKS:
        page_name = page_names.get(chunk_id, page_name)
        chunk_data = _chunk(controller, chunk_id)
        page_total = 0.0
        components = {}
        for comp_name, items in chunk_data.items():
            comp_total = 0.0
            active_items = []
            for item in items or []:
                if item.get("state", {}).get("in_trash", False):
                    continue
                values = item.get("values", {})
                item_total = (
                    _as_float(values.get("quantity"))
                    * _as_float(values.get("rate"))
                )
                comp_total += item_total
                active_items.append({**item, "total": item_total})
            components[comp_name] = {"items": active_items, "total": comp_total}
            page_total += comp_total
        pages_data[page_name] = {"components": components, "total": page_total}
        grand_total += page_total

    return {**pages_data, "grand_total": grand_total}


def _material_emissions_data(controller) -> dict:
    existing = _chunk(controller, "material_emissions_data")
    if existing:
        return existing

    total = 0.0
    included_items = []
    for chunk_id, category, _caption in STRUCTURE_CHUNKS:
        chunk_data = _chunk(controller, chunk_id)
        for comp_name, items in chunk_data.items():
            for item in items or []:
                if item.get("state", {}).get("in_trash", False):
                    continue
                state = item.get("state", {})
                if state.get("included_in_carbon_emission") is not True:
                    continue
                values = item.get("values", {})
                qty = _as_float(values.get("quantity"))
                cf = _as_float(values.get("conversion_factor"), 1.0)
                ef = _as_float(values.get("carbon_emission"))
                item_total = qty * cf * ef
                total += item_total
                included_items.append({
                    "category": category,
                    "component": comp_name,
                    "material": values.get("material_name", ""),
                    "quantity": qty,
                    "unit": values.get("unit", ""),
                    "conversion_factor": cf,
                    "carbon_emission": ef,
                    "carbon_unit": values.get("carbon_unit", ""),
                    "total_kgCO2e": item_total,
                })

    return {"total_kgCO2e": total, "included_items": included_items}


def _transport_emissions_data(controller) -> dict:
    existing = _chunk(controller, "transport_emissions_data")
    if existing:
        return existing

    transport = _chunk(controller, "transport_data")
    total = 0.0
    rows = []
    for entry in transport.get("vehicles", []) or []:
        if entry.get("state", {}).get("in_trash", False):
            continue
        summary = entry.get("summary", {})
        emission = _as_float(summary.get("total_emissions_kgco2e"))
        total += emission
        rows.append({
            "vehicle": entry.get("vehicle", {}),
            "route": entry.get("route", {}),
            "summary": summary,
            "total_kgCO2e": emission,
        })
    return {"total_kgCO2e": total, "rows": rows}


def _recycling_data(controller) -> dict:
    existing = _chunk(controller, "recycling_data")
    if existing:
        return existing

    total = 0.0
    for chunk_id, _category, _caption in STRUCTURE_CHUNKS:
        chunk_data = _chunk(controller, chunk_id)
        for items in chunk_data.values():
            for item in items or []:
                if item.get("state", {}).get("in_trash", False):
                    continue
                values = item.get("values", {})
                if item.get("state", {}).get("included_in_recyclability", True) is not True:
                    continue
                qty = _as_float(values.get("quantity"))
                pct = _as_float(
                    values.get("post_demolition_recovery_percentage")
                    or values.get("recyclability_percentage")
                )
                scrap = _as_float(values.get("scrap_rate"))
                total += qty * (pct / 100.0) * scrap
    return {"total_recovered_value": total}


def _all_current_data(controller) -> dict:
    bridge = _chunk(controller, "bridge_data")
    return {
        "bridge_data": bridge,
        "financial_data": _chunk(controller, "financial_data"),
        "maintenance_data": _chunk(controller, "maintenance_data"),
        "demolition_data": _chunk(controller, "demolition_data"),
        "traffic_and_road_data": _chunk(controller, "traffic_and_road_data"),
        "construction_work_data": _construction_work_data(controller),
        "recycling_data": _recycling_data(controller),
        "carbon_emission_data": {
            "social_cost_data": _chunk(controller, "social_cost_data"),
            "diversion_emissions": _chunk(controller, "diversion_emissions"),
            "material_emissions_data": _material_emissions_data(controller),
            "transport_emissions_data": _transport_emissions_data(controller),
            "machinery_emissions_data": _chunk(controller, "machinery_emissions_data"),
        },
        "analysis_period": _chunk(controller, "analysis_period").get(
            "analysis_period", bridge.get("analysis_period", 0)
        ),
    }


def _calculated_cache(controller) -> dict:
    try:
        from three_ps_lcca_core.core.main import run_full_lcc_analysis
        from three_ps_lcca_gui.gui.components.outputs.data_preparer import DataPreparer

        all_data = _all_current_data(controller)
        analysis_period = int(
            all_data.get("analysis_period")
            or all_data.get("bridge_data", {}).get("analysis_period")
            or 0
        )
        is_global, data_object = DataPreparer.prepare_data_object(all_data, analysis_period)
        wpi_metadata = None if is_global else DataPreparer.prepare_wpi_object(all_data)
        lcc_breakdown = DataPreparer.prepare_life_cycle_construction_cost(all_data)
        results = run_full_lcc_analysis(
            data_object, lcc_breakdown, wpi=wpi_metadata, debug=True
        )
        return {
            "is_valid": True,
            "analysis_period": analysis_period,
            "currency": _currency({}, controller),
            "all_data": all_data,
            "lcc_breakdown": lcc_breakdown,
            "results": results,
        }
    except Exception:
        return {}


def _sum_numbers(value, key: str = "") -> float:
    if isinstance(value, (int, float)):
        number = float(value)
        return -number if key in CREDIT_KEYS else number
    if isinstance(value, dict):
        return sum(_sum_numbers(v, k) for k, v in value.items())
    if isinstance(value, list):
        return sum(_sum_numbers(v) for v in value)
    return 0.0


def _stage_total(results: dict, stage_key: str) -> float:
    return _sum_numbers(results.get(stage_key, {}))


def _pillar_total(results: dict, pillar_key: str) -> float:
    total = 0.0
    for stage_key, _stage_label in STAGES:
        total += _sum_numbers(results.get(stage_key, {}).get(pillar_key, {}))
    return total


def _dict_rows(data: dict) -> list[list]:
    rows = []
    for key, value in data.items():
        if isinstance(value, dict):
            rows.extend(_dict_rows(value))
        else:
            display_value = -value if key in CREDIT_KEYS and isinstance(value, (int, float)) else value
            rows.append([str(key).replace("_", " ").title(), _fmt(display_value, 2)])
    return rows


def _rename_first_caption(latex: str, caption: str) -> str:
    if not latex:
        return ""
    latex = re.sub(r"\\caption\{[^{}]*\}", r"\\caption{" + caption + "}", latex, count=1)
    latex = latex.replace("â€”", "-")
    return _keep_table_here(latex)


class _CacheController:
    def __init__(self, cache: dict):
        self._cache = cache

    def get_chunk(self, name: str):
        return self._cache if name == "comparison_cache" else {}


def _main_lcc_table(controller, cache: dict) -> str:
    try:
        out = results_to_latex(_CacheController(cache)) or ""
    except Exception:
        out = ""
    out = _rename_first_caption(out, "Contribution of different life cycle cost components")
    if out:
        return out
    return _table(
        "Contribution of different life cycle cost components",
        "tab:lcc_components",
        ["Description", "Category", "Present Value"],
        [[EMDASH, EMDASH, EMDASH]],
        r"p{8cm}p{3cm}>{\raggedleft\arraybackslash}p{3cm}",
    )


def _stage_costs_table(controller, cache: dict) -> str:
    results = _results(cache)
    rows = [[label, _fmt(_stage_total(results, key), 2)] for key, label in STAGES if results.get(key)]
    return _table(
        "Life cycle stage wise costs",
        "tab:stage_costs",
        ["Life cycle stage", f"Cost ({_currency(cache, controller)})"],
        rows,
        r"p{9cm}>{\raggedleft\arraybackslash}p{4cm}",
    )


def _pillar_costs_table(controller, cache: dict) -> str:
    results = _results(cache)
    rows = [[label, _fmt(_pillar_total(results, key), 2)] for key, label in PILLARS]
    return _table(
        "Sustainability pillar wise cost",
        "tab:pillar_costs",
        ["Sustainability pillar", f"Cost ({_currency(cache, controller)})"],
        rows,
        r"p{9cm}>{\raggedleft\arraybackslash}p{4cm}",
    )


def _pillar_detail_table(controller, cache: dict, pillar_key: str, caption: str, label: str) -> str:
    results = _results(cache)
    rows = []
    for stage_key, stage_label in STAGES:
        data = results.get(stage_key, {}).get(pillar_key, {})
        for item_label, value in _dict_rows(data):
            rows.append([stage_label, item_label, value])
    return _table(
        caption,
        label,
        ["Stage", "Cost component", f"Cost ({_currency(cache, controller)})"],
        rows,
        r"p{3cm}p{7cm}>{\raggedleft\arraybackslash}p{4cm}",
    )


def _ruc_construction_table(controller, cache: dict) -> str:
    results = _results(cache)
    social = results.get("initial_stage", {}).get("social", {})
    rows = _dict_rows(social)
    return _table(
        "Road user costs during construction",
        "tab:ruc_construction",
        ["Cost component", f"Cost ({_currency(cache, controller)})"],
        rows,
        r"p{9cm}>{\raggedleft\arraybackslash}p{4cm}",
    )


def lcca_results_to_latex(controller=None) -> str:
    cache = _cache(controller)
    return "\n\n".join(part for part in [
        section("LCCA results"),
        subsection("Life cycle cost results"),
        _main_lcc_table(controller, cache),
        placeholder_figure("LCC components results"),
        subsection("Stage-wise distribution of life cycle costs"),
        _stage_costs_table(controller, cache),
        subsection("Pillar-wise distribution of life cycle costs"),
        _pillar_costs_table(controller, cache),
        placeholder_figure("Distribution of 3PS and 3 stages of LCC"),
        subsubsection("Economic costs"),
        _pillar_detail_table(controller, cache, "economic", "Economic cost results across different stages", "tab:economic_costs"),
        subsubsection("Social costs"),
        _pillar_detail_table(controller, cache, "social", "Social cost across different stages", "tab:social_costs"),
        _ruc_construction_table(controller, cache),
        placeholder_figure("Distribution of various components of road user cost during construction"),
        subsubsection("Environmental costs"),
        _pillar_detail_table(controller, cache, "environmental", "Environmental costs across different stages", "tab:environmental_costs"),
    ] if part and part.strip())
