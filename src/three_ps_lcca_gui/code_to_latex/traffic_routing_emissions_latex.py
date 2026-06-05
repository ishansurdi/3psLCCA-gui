import pandas as pd

from ..gui.project_controller import ProjectController
from .chunks import DIVERSION_EMISSIONS_CHUNK, TRAFFIC_AND_ROAD_DATA_CHUNK

VEHICLES = [
    ("small_cars", "Small Car"),
    ("big_cars", "Big Car"),
    ("two_wheelers", "Two Wheeler"),
    ("o_buses", "Ordinary Buses"),
    ("d_buses", "Deluxe Buses"),
    ("lcv", "LCV"),
    ("hcv", "HCV"),
    ("mcv", "MCV"),
]

DEFAULT_FACTORS = {
    "small_cars": 0.1030,
    "big_cars": 0.2690,
    "two_wheelers": 0.0351,
    "o_buses": 0.4548,
    "d_buses": 0.6064,
    "lcv": 0.3070,
    "hcv": 0.5928,
    "mcv": 0.7375,
}


def _fmt_number(value, decimals=3) -> str:
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "--"


def _fmt_int(value) -> str:
    try:
        return f"{int(float(value)):,}"
    except (TypeError, ValueError):
        return "--"


def _calculated_to_latex(emissions_data: dict, traffic_data: dict) -> str:
    vehicle_data = traffic_data.get("vehicle_data", {})
    factors = emissions_data.get("emission_factors", {})
    reroute_km = float(traffic_data.get("additional_reroute_distance_km", 0) or 0)

    rows = []
    for key, label in VEHICLES:
        vehicles_per_day = int(float((vehicle_data.get(key) or {}).get("vehicles_per_day", 0) or 0))
        emission_factor = float(factors.get(key, DEFAULT_FACTORS.get(key, 0.0)) or 0)
        emission = vehicles_per_day * emission_factor * reroute_km

        rows.append([
            label,
            _fmt_int(vehicles_per_day),
            _fmt_number(emission_factor),
            _fmt_number(reroute_km),
            _fmt_number(emission),
        ])

    df = pd.DataFrame(
        rows,
        columns=[
            "Vehicle Type",
            "Vehicles / Day",
            "Emission Factor kgCO2e/veh-km/day",
            "Reroute Distance km",
            "Emissions kgCO2e/day",
        ],
    )

    return df.to_latex(
        index=False,
        caption="Traffic Rerouting Emissions",
        label="tab:traffic_rerouting_emissions",
        escape=True,
        longtable=True,
    )


def _direct_to_latex(emissions_data: dict) -> str:
    direct_emissions = emissions_data.get("total_direct_emissions", 0)

    df = pd.DataFrame(
        [["Total Direct Rerouting Emissions", _fmt_number(direct_emissions)]],
        columns=["Input", "Emissions kgCO2e/day"],
    )

    return df.to_latex(
        index=False,
        caption="Direct Traffic Rerouting Emissions",
        label="tab:direct_traffic_rerouting_emissions",
        escape=True,
        longtable=True,
    )


def traffic_routing_emissions_to_latex(controller: ProjectController) -> str:
    emissions_data = controller.engine.fetch_chunk(DIVERSION_EMISSIONS_CHUNK) or {}
    traffic_data = controller.engine.fetch_chunk(TRAFFIC_AND_ROAD_DATA_CHUNK) or {}

    mode = emissions_data.get("mode", "Calculate by Vehicle")

    if mode == "Enter Directly":
        return _direct_to_latex(emissions_data)

    return _calculated_to_latex(emissions_data, traffic_data)