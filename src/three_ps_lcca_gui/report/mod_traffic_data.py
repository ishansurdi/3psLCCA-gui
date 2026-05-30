
from pylatex import Section, Subsection, Tabular, NoEscape
from pylatex.utils import bold, escape_latex
from .constants import (
    KEY_SHOW_AVG_TRAFFIC, KEY_AVG_TRAFFIC,
    KEY_SHOW_ROAD_TRAFFIC, KEY_ROAD_TRAFFIC,
    KEY_SHOW_PEAK_HOUR, KEY_PEAK_HOUR,
    KEY_SHOW_HUMAN_INJURY, KEY_HUMAN_INJURY,
    KEY_SHOW_VEHICLE_DAMAGE, KEY_VEHICLE_DAMAGE,
    KEY_SHOW_TYRE_COST, KEY_TYRE_COST,
    KEY_SHOW_FUEL_OIL, KEY_FUEL_OIL,
    KEY_SHOW_NEW_VEHICLE, KEY_NEW_VEHICLE,
)

# 2-col: avg daily traffic (10 : 4.5 → 0.690 : 0.310)
_COL_AVG_TRAFFIC = r"|p{\colw{0.690}}|p{\colw{0.310}}|"

# 2-col: peak hour / human injury / vehicle damage (7 : 7.5 → 0.483 : 0.517)
_COL_HALF = r"|p{\colw{0.483}}|p{\colw{0.517}}|"

# 4-col: tyre cost (3.5 : 2.0 : 3.0 : 2.0 → /10.5)
_COL_TYRE = (
    r"|p{\colw{0.333}}|p{\colw{0.190}}|p{\colw{0.286}}|p{\colw{0.190}}|"
)

# 3-col: new vehicle cost (4.5 : 3.5 : 3.0 → /11.0)
_COL_NEW_VEHICLE = (
    r"|p{\colw{0.409}}|p{\colw{0.318}}|p{\colw{0.273}}|"
)


def _format_traffic_count(value):
    if isinstance(value, bool):
        return str(value)

    text = str(value).strip()
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not value.is_integer():
            return f"{value:,.2f}".rstrip("0").rstrip(".")
        return f"{int(value):,}"

    cleaned = text.replace(",", "")
    if cleaned.replace(".", "", 1).isdigit():
        if "." in cleaned:
            numeric = float(cleaned)
            if numeric.is_integer():
                return f"{int(numeric):,}"
            return f"{numeric:,.2f}".rstrip("0").rstrip(".")
        return f"{int(cleaned):,}"

    return text


def add_traffic_data(doc, config, data):
    """Adds the Traffic Analysis tables to the report."""

    # Check if any traffic subsection is enabled
    traffic_keys = [
        KEY_SHOW_AVG_TRAFFIC, KEY_SHOW_ROAD_TRAFFIC, KEY_SHOW_PEAK_HOUR,
        KEY_SHOW_HUMAN_INJURY, KEY_SHOW_VEHICLE_DAMAGE,
        KEY_SHOW_TYRE_COST, KEY_SHOW_FUEL_OIL, KEY_SHOW_NEW_VEHICLE,
    ]
    if not any(config.get(k, False) for k in traffic_keys):
        return

    with doc.create(Subsection("Traffic data")):
        doc.append("Average daily traffic by vehicle class, rerouting distance, "
                   "construction duration, vehicle operating cost and value of "
                   "time parameters.")

        # ── 2.4.1 Average Daily Traffic ──────────────────────────────────
        if config.get(KEY_SHOW_AVG_TRAFFIC, True):
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{12\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Average Daily Traffic for each vehicle}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            with doc.create(Tabular(NoEscape(_COL_AVG_TRAFFIC))) as t:
                t.add_hline()
                t.add_row([bold("Vehicle type"), bold("Vehicles/day")])
                t.add_hline()
                for key, val in data.get(KEY_AVG_TRAFFIC, {}).items():
                    t.add_row([
                        escape_latex(key),
                        escape_latex(_format_traffic_count(val)),
                    ])
                    t.add_hline()
            doc.append(NoEscape(r"\vspace{4pt}"))

        # ── 2.4.2 Road traffic data ──────────────────────────────────────
        if config.get(KEY_SHOW_ROAD_TRAFFIC, True):
            doc.add_kv_table(
                "Road and traffic related data",
                data.get(KEY_ROAD_TRAFFIC, {}),
                key_frac=0.62,
            )

        # ── 2.4.3 Peak hour distribution ─────────────────────────────────
        if config.get(KEY_SHOW_PEAK_HOUR, True):
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{8\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Peak hour distribution}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            with doc.create(Tabular(NoEscape(_COL_HALF))) as t:
                t.add_hline()
                t.add_row([bold("Hour Category"), bold("Traffic proportion")])
                t.add_hline()
                for key, val in data.get(KEY_PEAK_HOUR, {}).items():
                    t.add_row([escape_latex(key), escape_latex(str(val))])
                    t.add_hline()
            doc.append(NoEscape(r"\vspace{4pt}"))

        # ── 2.4.4 Human injury cost ──────────────────────────────────────
        if config.get(KEY_SHOW_HUMAN_INJURY, True):
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{8\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Human injury cost data}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            with doc.create(Tabular(NoEscape(_COL_HALF))) as t:
                t.add_hline()
                t.add_row([
                    bold("Category of accident"),
                    NoEscape(r"\textbf{Accident distribution (\%)}"),
                ])
                t.add_hline()
                for key, val in data.get(KEY_HUMAN_INJURY, {}).items():
                    t.add_row([escape_latex(key), escape_latex(str(val))])
                    t.add_hline()
            doc.append(NoEscape(r"\vspace{4pt}"))

        # ── 2.4.5 Vehicle damage cost ────────────────────────────────────
        if config.get(KEY_SHOW_VEHICLE_DAMAGE, True):
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{12\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Vehicle damage cost data}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            with doc.create(Tabular(NoEscape(_COL_HALF))) as t:
                t.add_hline()
                t.add_row([
                    bold("Vehicle type"),
                    NoEscape(r"\textbf{Percentage of accidents for each vehicle type}"),
                ])
                t.add_hline()
                for key, val in data.get(KEY_VEHICLE_DAMAGE, {}).items():
                    t.add_row([escape_latex(key), escape_latex(str(val))])
                    t.add_hline()
            doc.append(NoEscape(r"\vspace{4pt}"))

        # ── 2.4.6 Tyre cost data ─────────────────────────────────────────
        if config.get(KEY_SHOW_TYRE_COST, True):
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{12\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Cost of tyres for different vehicle types}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            with doc.create(Tabular(NoEscape(_COL_TYRE))) as t:
                t.add_hline()
                t.add_row([
                    bold("Vehicle type"),
                    bold("No. of wheels"),
                    bold("Cost per tyre"),
                    bold("WPI Ratio"),
                ])
                t.add_hline()
                for vtype, vals in data.get(KEY_TYRE_COST, {}).items():
                    t.add_row([escape_latex(vtype)] +
                              [escape_latex(str(v)) for v in vals])
                    t.add_hline()
            doc.append(NoEscape(r"\vspace{4pt}"))

        # ── 2.4.7 Fuel, oil and grease ───────────────────────────────────
        if config.get(KEY_SHOW_FUEL_OIL, True):
            doc.add_kv_table(
                "Cost of fuel, lubricating oil and grease",
                data.get(KEY_FUEL_OIL, {}),
                key_frac=0.62,
            )

        # ── 2.4.8 New vehicle cost ───────────────────────────────────────
        if config.get(KEY_SHOW_NEW_VEHICLE, True):
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{12\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Cost of new vehicle for different vehicle types}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            with doc.create(Tabular(NoEscape(_COL_NEW_VEHICLE))) as t:
                t.add_hline()
                t.add_row([
                    bold("Vehicle type"),
                    bold("Cost of new vehicle"),
                    bold("Depreciation"),
                ])
                t.add_hline()
                for vtype, vals in data.get(KEY_NEW_VEHICLE, {}).items():
                    t.add_row([escape_latex(vtype)] +
                              [escape_latex(str(v)) for v in vals])
                    t.add_hline()
            doc.append(NoEscape(r"\vspace{4pt}"))

