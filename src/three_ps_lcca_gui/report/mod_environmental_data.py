from pylatex import Subsection, Tabular, NoEscape
from pylatex.utils import bold, escape_latex
from .constants import (
    KEY_SHOW_SOCIAL_CARBON, KEY_SOCIAL_CARBON,
    KEY_SHOW_MATERIAL_EMISSION, KEY_MATERIAL_EMISSION,
    KEY_SHOW_USE_EMISSION, KEY_USE_EMISSION,
    KEY_SHOW_VEHICLE_EMISSION, KEY_VEHICLE_EMISSION,
    KEY_SHOW_TRANSPORT_EMISSION, KEY_TRANSPORT_EMISSION,
    KEY_SHOW_ONSITE_EMISSION, KEY_ONSITE_EMISSION,
)

# 7-col: material emission
_COL_MATERIAL_EMISSION = (
    r"|>{\raggedright\arraybackslash}p{\colw{0.165}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.241}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.098}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.075}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.135}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.135}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.150}}|"
)

# 8-col: transport emission
_COL_TRANSPORT = (
    r"|p{\colw{0.149}}|p{\colw{0.149}}|p{\colw{0.097}}"
    r"|p{\colw{0.112}}|p{\colw{0.112}}|p{\colw{0.112}}"
    r"|p{\colw{0.112}}|p{\colw{0.157}}|"
)

# 6-col: onsite emission
_COL_ONSITE = (
    r"|p{\colw{0.220}}|p{\colw{0.157}}|p{\colw{0.181}}"
    r"|p{\colw{0.118}}|p{\colw{0.142}}|p{\colw{0.181}}|"
)

# 2-col: use/vehicle emission
_COL_USE_EMISSION = r"|p{\colw{0.643}}|p{\colw{0.357}}|"


def add_environmental_data(doc, config, data):
    """Section 2.5: Environmental input data - Tables 2-14 to 2-19."""

    # Check if any environmental subsection is enabled
    env_keys = [
        KEY_SHOW_SOCIAL_CARBON, KEY_SHOW_MATERIAL_EMISSION,
        KEY_SHOW_USE_EMISSION, KEY_SHOW_VEHICLE_EMISSION,
        KEY_SHOW_TRANSPORT_EMISSION, KEY_SHOW_ONSITE_EMISSION,
    ]
    if not any(config.get(k, False) for k in env_keys):
        return

    with doc.create(Subsection("Environmental input data")):
        doc.append(
            "Emission factors for construction and traffic activities "
            "and carbon pricing assumptions."
        )

        # ── Table 2-14: Social Cost of Carbon ────────────────────────

        # ── Table 2-14: Social Cost of Carbon ────────────────────────
        if config.get(KEY_SHOW_SOCIAL_CARBON, True):
            doc.add_kv_table(
                "Social Cost of Carbon",
                data.get(KEY_SOCIAL_CARBON, {}),
                key_frac=0.62,
                need_lines=2,
            )

        # ── Table 2-15: Material Emission Factors ────────────────────
        if config.get(KEY_SHOW_MATERIAL_EMISSION, True):
            rows_tex = ""
            for mat, vals in data.get(KEY_MATERIAL_EMISSION, {}).items():
                category = (
                    NoEscape(r"\parbox[t]{\linewidth}{\raggedright\hspace{0pt}\seqsplit{" + escape_latex(str(vals[0])) + r"}}")
                    if len(vals) > 0 else ""
                )
                material = NoEscape(r"\parbox[t]{\linewidth}{\raggedright\hspace{0pt}\seqsplit{" + escape_latex(mat) + r"}}")
                row = [category, material] + [escape_latex(str(v)) for v in vals[1:]]
                rows_tex += " & ".join(row) + r" \\" + "\n"
                rows_tex += r"\hline" + "\n"

            header_row = (
                r"\rowcolor{gray!10}"
                + r"\textbf{Category} & \textbf{Material} & \textbf{Quantity}"
                + r" & \textbf{Unit} & \textbf{Conversion factor}"
                + r" & \textbf{Emission factor} & \textbf{Emission factor unit} \\"
            )
            caption_tex = r"\caption{Material related factors for emission}\\" + "\n"
            longtable_tex = (
                r"{\footnotesize" + "\n"
                + r"\begin{longtable}{" + _COL_MATERIAL_EMISSION + r"}" + "\n"
                + caption_tex
                + r"\hline" + "\n"
                + header_row + "\n"
                + r"\hline" + "\n"
                + r"\endfirsthead" + "\n"
                + r"\hline" + "\n"
                + header_row + "\n"
                + r"\hline" + "\n"
                + r"\endhead" + "\n"
                + r"\hline" + "\n"
                + r"\endfoot" + "\n"
                + r"\endlastfoot" + "\n"
                + rows_tex
                + r"\end{longtable}" + "\n"
                + r"}"
            )
            doc.append(NoEscape(longtable_tex))
            doc.append(NoEscape(r"\vspace{4pt}"))

        # ── Table 2-16: Use Stage Emission Assumptions ───────────────
        if config.get(KEY_SHOW_USE_EMISSION, True):
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{5\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Assumptions for use stage "
                r"and end of life emissions}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            with doc.create(Tabular(NoEscape(_COL_USE_EMISSION))) as t:
                t.add_hline()
                t.add_row(["", bold("Assumed \\% of initial emission")])
                t.add_hline()
                for key, val in data.get(KEY_USE_EMISSION, {}).items():
                    t.add_row([escape_latex(key), escape_latex(str(val))])
                    t.add_hline()
            doc.append(NoEscape(r"\vspace{4pt}"))

        # ── Table 2-17: Vehicle Emission Factors ─────────────────────
        if config.get(KEY_SHOW_VEHICLE_EMISSION, True):
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{5\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Vehicle related emission factors}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            with doc.create(Tabular(NoEscape(_COL_USE_EMISSION))) as t:
                t.add_hline()
                t.add_row([bold("Vehicle type"), bold("Emission factor")])
                t.add_hline()
                for key, val in data.get(KEY_VEHICLE_EMISSION, {}).items():
                    t.add_row([escape_latex(key), escape_latex(str(val))])
                    t.add_hline()
            doc.append(NoEscape(r"\vspace{4pt}"))

        # ── Table 2-18: Transport Emissions ──────────────────────────
        if config.get(KEY_SHOW_TRANSPORT_EMISSION, True):
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{6\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Data for emissions related to "
                r"transportation of material}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"{\footnotesize"))
            with doc.create(Tabular(NoEscape(_COL_TRANSPORT))) as t:
                t.add_hline()
                t.add_row([
                    bold("Transport Material"),
                    bold("Vehicle name"),
                    NoEscape(r"\textbf{GVW (tonne)}"),
                    NoEscape(r"\textbf{Cargo capacity (tonne)}"),
                    NoEscape(r"\textbf{Distance travelled (km)}"),
                    bold("Source"),
                    bold("Destination"),
                    NoEscape(r"\textbf{Emission Factor (kgCO\textsubscript{2}e/tonne-km)}"),
                ])
                t.add_hline()
                for mat, vals in data.get(KEY_TRANSPORT_EMISSION, {}).items():
                    t.add_row([escape_latex(mat)] +
                              [escape_latex(str(v)) for v in vals])
                    t.add_hline()
            doc.append(NoEscape(r"}"))
            doc.append(NoEscape(r"\vspace{4pt}"))

        # ── Table 2-19: On-site Emissions ────────────────────────────
        if config.get(KEY_SHOW_ONSITE_EMISSION, True):
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{6\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Emissions from on-site "
                r"activities during construction}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"{\footnotesize"))
            with doc.create(Tabular(NoEscape(_COL_ONSITE))) as t:
                t.add_hline()
                t.add_row([
                    bold("Construction Equipment"),
                    bold("Energy Source"),
                    NoEscape(r"\textbf{Diesel consumption (l/hour) or Electricity (Kw)}"),
                    NoEscape(r"\textbf{Avg number of hours used per day}"),
                    NoEscape(r"\textbf{Number of days the equipment would be used}"),
                    NoEscape(r"\textbf{Emission factor (kgCO\textsubscript{2}e/unit)}"),
                ])
                t.add_hline()
                for equip, vals in data.get(KEY_ONSITE_EMISSION, {}).items():
                    row_vals = list(vals)[:5]
                    t.add_row([escape_latex(equip)] +
                              [escape_latex(str(v)) for v in row_vals])
                    t.add_hline()
            doc.append(NoEscape(r"}"))
            doc.append(NoEscape(r"\vspace{4pt}"))
