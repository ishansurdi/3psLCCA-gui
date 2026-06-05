import pandas as pd
from ...gui.components.traffic_data.main import TRAFFIC_FIELDS, _BY_CODE
from ..common_code import fields_to_latex
from ..SETTINGS import DECIMAL_PLACES_FOR_LATEX


def _traffic_fields(data: dict) -> str:
    display_data = dict(data)
    code = display_data.get("alternate_road_carriageway", "")
    display_data["alternate_road_carriageway"] = _BY_CODE.get(code, code)

    return fields_to_latex(
        TRAFFIC_FIELDS,
        display_data,
        "Traffic and Road Data",
        "tab:traffic_and_road_data",
    )


def _peak_hour_distribution(data: dict) -> str:
    peak_data = data.get("peak_hour_distribution", {})
    n = data.get("num_peak_hours", len(peak_data))

    rows = []
    for i in range(1, int(n) + 1):
        val = peak_data.get(f"peak_hour_{i}")
        rows.append({
            "Hour": f"Peak Hour {i}",
            r"Traffic Proportion (\%)": val * 100 if val is not None else None,
        })

    df = pd.DataFrame(rows)
    return (
        df.style
        .hide(axis="index")
        .format(
            {r"Traffic Proportion (\%)": f"{{:.{DECIMAL_PLACES_FOR_LATEX}f}}"},
            na_rep=r"\textemdash",
        )
        .to_latex(
            caption="Peak Hour Traffic Distribution",
            label="tab:peak_hour_distribution",
            hrules=True,
            column_format="lr",
            position="h!",
            position_float="centering",
        )
    ) or ""
