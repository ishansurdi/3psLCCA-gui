import pandas as pd

from ..gui.project_controller import ProjectController

CHUNK = "machinery_emissions_data"


def _fmt_number(value, decimals=2) -> str:
    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "--"


def _fmt_int(value) -> str:
    try:
        return f"{int(float(value))}"
    except (TypeError, ValueError):
        return "--"


def _detailed_to_latex(data: dict) -> str:
    rows = data.get("detailed", {}).get("rows", [])

    table_rows = []
    for row in rows:
        name = row.get("name", "")
        source = row.get("source", "")
        rate = float(row.get("rate", 0) or 0)
        hrs = float(row.get("hrs", 0) or 0)
        days = int(float(row.get("days", 0) or 0))
        ef = float(row.get("ef", 0) or 0)

        consumption = rate * hrs * days
        emission = consumption * ef

        table_rows.append([
            name,
            source,
            _fmt_number(rate),
            _fmt_number(hrs),
            _fmt_int(days),
            _fmt_number(ef),
            _fmt_number(consumption),
            _fmt_number(emission),
        ])

    df = pd.DataFrame(
        table_rows,
        columns=[
            "Equipment Name",
            "Energy Source",
            "Fuel / Power Rating",
            "Avg Hrs/Day",
            "No. of Days",
            "EF kg CO2e/unit",
            "Consumption",
            "Emissions kg CO2e",
        ],
    )

    return df.to_latex(
        index=False,
        caption="Machinery and Equipment Emissions",
        label="tab:machinery_equipment_emissions",
        escape=True,
        longtable=True,
    )


def _lumpsum_to_latex(data: dict) -> str:
    lumpsum = data.get("lumpsum", {})

    elec_consumption = float(lumpsum.get("elec_consumption_per_day", 0) or 0)
    elec_days = int(float(lumpsum.get("elec_days", 0) or 0))
    elec_ef = float(lumpsum.get("elec_ef", 0) or 0)
    elec_emission = elec_consumption * elec_days * elec_ef

    fuel_consumption = float(lumpsum.get("fuel_consumption_per_day", 0) or 0)
    fuel_days = int(float(lumpsum.get("fuel_days", 0) or 0))
    fuel_ef = float(lumpsum.get("fuel_ef", 0) or 0)
    fuel_emission = fuel_consumption * fuel_days * fuel_ef

    df = pd.DataFrame(
        [
            [
                "Electricity",
                _fmt_number(elec_consumption),
                _fmt_int(elec_days),
                _fmt_number(elec_ef),
                _fmt_number(elec_emission),
            ],
            [
                "Fuel",
                _fmt_number(fuel_consumption),
                _fmt_int(fuel_days),
                _fmt_number(fuel_ef),
                _fmt_number(fuel_emission),
            ],
        ],
        columns=[
            "Source",
            "Consumption / Day",
            "Days",
            "EF",
            "Emissions kg CO2e",
        ],
    )

    return df.to_latex(
        index=False,
        caption="Lump Sum Machinery and Equipment Emissions",
        label="tab:lumpsum_machinery_equipment_emissions",
        escape=True,
        longtable=True,
    )


def machinery_emissions_to_latex(controller: ProjectController) -> str:
    data = controller.engine.fetch_chunk(CHUNK) or {}
    mode = data.get("mode", "detailed")

    if mode == "lumpsum":
        return _lumpsum_to_latex(data)

    return _detailed_to_latex(data)