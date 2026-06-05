from ...gui.components.utils.common_requested_data import get_traffic_and_road_data
from .wpi_tables_latex import _get_wpi_base, _get_wpi_ratio, _get_wpi_selected
from .vehicle_data_latex import _vehicle_data
from .all_fields_latex import _traffic_fields, _peak_hour_distribution


def _wpi_base(data: dict) -> str:
    snapshot = data.get("wpi", {}).get("data_snapshot", {})
    return _get_wpi_base(snapshot.get("base", {}))


def _wpi_selected(data: dict) -> str:
    snapshot = data.get("wpi", {}).get("data_snapshot", {})
    return _get_wpi_selected(snapshot.get("selected", {}))


def _wpi_ratio(data: dict) -> str:
    snapshot = data.get("wpi", {}).get("data_snapshot", {})
    return _get_wpi_ratio(snapshot.get("ratio", {}))


# ── Individual devmode entries (each fetches once for its own use) ─────────────

def traffic_fields_to_latex(controller=None) -> str:
    return _traffic_fields(get_traffic_and_road_data())


def peak_hour_distribution_to_latex(controller=None) -> str:
    return _peak_hour_distribution(get_traffic_and_road_data())


def vehicle_data_to_latex(controller=None) -> str:
    return _vehicle_data(get_traffic_and_road_data())


def wpi_base_to_latex(controller=None) -> str:
    return _wpi_base(get_traffic_and_road_data())


def wpi_selected_to_latex(controller=None) -> str:
    return _wpi_selected(get_traffic_and_road_data())


def wpi_ratio_to_latex(controller=None) -> str:
    return _wpi_ratio(get_traffic_and_road_data())


# ── Full page: fetch once, pass to every section ───────────────────────────────

def traffic_and_road_data_to_latex(controller=None) -> str:
    data = get_traffic_and_road_data()
    return "\n\n".join([
        _traffic_fields(data),
        _vehicle_data(data),
        _peak_hour_distribution(data),
        _wpi_base(data),
        _wpi_selected(data),
        _wpi_ratio(data),
    ])
