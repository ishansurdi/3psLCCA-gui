"""
Shared helpers for fetching commonly needed values from the general_info chunk.

Usage:
    # once, when the controller is created (e.g. in ProjectManager / ProjectWindow):
    from ...components.utils.common_requested_data import set_controller
    set_controller(controller)

    # anywhere in the UI — no argument needed:
    from ...components.utils.common_requested_data import get_currency
    currency = get_currency()   # returns "" if no project is active
"""

from __future__ import annotations

_GENERAL_INFO_CHUNK = "general_info"
_controller = None


def set_controller(controller) -> None:
    global _controller
    _controller = controller


def get_currency() -> str:
    """Return the project currency string from general_info, or 'Currency' if unavailable."""
    try:
        if _controller and _controller.engine:
            gen = _controller.engine.fetch_chunk(_GENERAL_INFO_CHUNK) or {}
            return gen.get("project_currency", "") or "Currency"
    except Exception:
        pass
    return "Currency"
