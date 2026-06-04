"""
Shared helpers for fetching commonly needed values from project chunks.

Usage:
    # Once, when the controller is created (e.g. in ProjectManager):
    from ...components.utils.common_requested_data import set_controller
    set_controller(controller)

    # Anywhere in the UI — no argument needed:
    from ...components.utils.common_requested_data import get_currency, get_bridge_data
    currency   = get_currency()
    bridge     = get_bridge_data()
"""

from __future__ import annotations

_controller = None


def set_controller(controller) -> None:
    global _controller
    _controller = controller


# ── Known chunks ─────────────────────────────────────────────────────────────

_ALL_CHUNKS = [
    "general_info",
    "bridge_data",
    "financial_data",
    "maintenance_data",
    "demolition_data",
    "traffic_and_road_data",
    "str_foundation",
    "str_sub_structure",
    "str_super_structure",
    "str_misc",
    "transport_data",
    "machinery_emissions_data",
    "social_cost_data",
    "diversion_emissions",
    "str_summary",
]


# ── Generic ───────────────────────────────────────────────────────────────────

def get_chunk(chunk_name: str) -> dict:
    """Return a chunk dict via the controller cache (always reflects latest save).

    Uses controller.get_chunk() — not engine.fetch_chunk() — so staged-but-not-yet-
    flushed saves are included. Always call this after save_chunk_data to get fresh data.
    """
    try:
        if _controller:
            return _controller.get_chunk(chunk_name) or {}
    except Exception:
        pass
    return {}


def get_all_data() -> dict:
    """Return all known chunks as a flat dict keyed by chunk name."""
    return {name: get_chunk(name) for name in _ALL_CHUNKS}


# ── general_info ──────────────────────────────────────────────────────────────

def get_general_info() -> dict:
    return get_chunk("general_info")


def get_currency() -> str:
    """Return the project currency string, or 'Currency' if unavailable."""
    return get_general_info().get("project_currency", "") or "Currency"


def get_project_country() -> str:
    return get_general_info().get("project_country", "")


def get_project_name() -> str:
    return get_general_info().get("project_name", "")


# ── bridge_data ───────────────────────────────────────────────────────────────

def get_bridge_data() -> dict:
    return get_chunk("bridge_data")


def get_design_life() -> int | None:
    val = get_bridge_data().get("design_life")
    return int(val) if val is not None else None


def get_analysis_period() -> int | None:
    val = get_bridge_data().get("analysis_period")
    return int(val) if val is not None else None


def get_construction_duration_months() -> float | None:
    val = get_bridge_data().get("duration_construction_months")
    return float(val) if val is not None else None


# ── financial_data ────────────────────────────────────────────────────────────

def get_financial_data() -> dict:
    return get_chunk("financial_data")


def get_discount_rate() -> float | None:
    val = get_financial_data().get("discount_rate")
    return float(val) if val is not None else None


# ── str_summary ───────────────────────────────────────────────────────────────

def get_str_summary() -> dict:
    """Return the auto-computed structure cost summary (read-only, always current)."""
    return get_chunk("str_summary")
