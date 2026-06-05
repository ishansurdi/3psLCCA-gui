import pandas as pd
from ...gui.components.traffic_data.wpi_table import _VEHICLES, _COLUMNS, _col_key
from ..SETTINGS import DECIMAL_PLACES_FOR_LATEX, DECIMAL_PLACES_FOR_LATEX_RATIO


def _wpi_to_styler(data: dict, fmt: str):
    col_keys   = [_col_key(c) for c in _COLUMNS]
    col_labels = [c.label      for c in _COLUMNS]

    rows = []
    for vkey, _ in _VEHICLES:
        vdata = data.get(vkey, {})
        rows.append([vdata.get(k) for k in col_keys])

    index = [label for _, label in _VEHICLES]
    df = pd.DataFrame(rows, index=index, columns=col_labels)
    df.index.name = "Vehicle"
    return df.style.format(fmt, na_rep=r"\textemdash")


def _get_wpi_base(data: dict) -> str:
    return _wpi_to_styler(data, f"{{:.{DECIMAL_PLACES_FOR_LATEX}f}}").to_latex(
        caption="WPI Base Adjustment Factors (2019 Base Year). All values in INR.",
        label="tab:wpi_base",
        hrules=True,
        column_format="l" + "r" * len(_COLUMNS),
        position="h!",
        position_float="centering",
    ) or ""


def _get_wpi_selected(data: dict) -> str:
    return _wpi_to_styler(data, f"{{:.{DECIMAL_PLACES_FOR_LATEX}f}}").to_latex(
        caption="WPI Selected Year Adjustment Factors. All values in INR.",
        label="tab:wpi_selected",
        hrules=True,
        column_format="l" + "r" * len(_COLUMNS),
        position="h!",
        position_float="centering",
    ) or ""


def _get_wpi_ratio(data: dict) -> str:
    return _wpi_to_styler(data, f"{{:.{DECIMAL_PLACES_FOR_LATEX_RATIO}f}}").to_latex(
        caption="WPI Adjustment Ratios (Selected / Base). All values in INR.",
        label="tab:wpi_ratio",
        hrules=True,
        column_format="l" + "r" * len(_COLUMNS),
        position="h!",
        position_float="centering",
    ) or ""


