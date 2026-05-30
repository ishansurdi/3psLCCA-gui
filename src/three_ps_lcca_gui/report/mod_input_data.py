
from pylatex import Section, Subsection, Tabular, NoEscape
from pylatex.utils import bold, escape_latex
from .constants import (
    KEY_SHOW_BRIDGE_DESC, KEY_BRIDGE_DESC,
    KEY_SHOW_FINANCIAL, KEY_FINANCIAL,
    KEY_SHOW_CONSTRUCTION, KEY_CONSTRUCTION,
    KEY_SHOW_LCC_ASSUMPTIONS, KEY_LCC_ASSUMPTIONS,
    KEY_SHOW_USE_STAGE, KEY_USE_STAGE,
    KEY_SHOW_AVG_TRAFFIC, KEY_AVG_TRAFFIC,
    KEY_SHOW_ROAD_TRAFFIC, KEY_ROAD_TRAFFIC,
    KEY_SHOW_PEAK_HOUR, KEY_PEAK_HOUR,
    KEY_SHOW_HUMAN_INJURY, KEY_HUMAN_INJURY,
    KEY_SHOW_VEHICLE_DAMAGE, KEY_VEHICLE_DAMAGE,
    KEY_SHOW_SOCIAL_CARBON, KEY_SOCIAL_CARBON,
    KEY_SHOW_MATERIAL_EMISSION, KEY_MATERIAL_EMISSION,
    KEY_SHOW_USE_EMISSION, KEY_USE_EMISSION,
    KEY_SHOW_VEHICLE_EMISSION, KEY_VEHICLE_EMISSION,
    KEY_SHOW_TRANSPORT_EMISSION, KEY_TRANSPORT_EMISSION,
    KEY_SHOW_ONSITE_EMISSION, KEY_ONSITE_EMISSION,
)

# ── Column specs using \colw{fraction} ───────────────────────────────────────
# All fractions within a spec sum to 1.0, so each table fills exactly \linewidth.

# 3-col: LCC assumptions (5.5 : 3.0 : 5.0 → 0.407 : 0.222 : 0.370)
_COL_LCC_ASSUMPTIONS = (
    r"|p{\colw{0.407}}|p{\colw{0.222}}|p{\colw{0.370}}|"
)

# 2-col: avg daily traffic (10 : 4.5 → 0.690 : 0.310)
_COL_AVG_TRAFFIC = r"|p{\colw{0.690}}|p{\colw{0.310}}|"

# 2-col: peak hour / human injury / vehicle damage (7 : 7.5 → 0.483 : 0.517)
_COL_HALF = r"|p{\colw{0.483}}|p{\colw{0.517}}|"

# 2-col: use/vehicle emission (9 : 5 → 0.643 : 0.357)
_COL_USE_EMISSION = r"|p{\colw{0.643}}|p{\colw{0.357}}|"

# 6-col: construction (Category : Material : Rate : Quantity : Unit : Source)
_COL_CONSTRUCTION = (
    r"|>{\centering\arraybackslash}p{\colw{0.200}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.230}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.150}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.160}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.080}}"
    r"|>{\raggedright\arraybackslash}p{\colw{0.180}}|"
)

# 7-col: material emission (2.2 : 3.2 : 1.3 : 1.0 : 1.8 : 1.8 : 2.0 → /13.3)
_COL_MATERIAL_EMISSION = (
    r"|p{\colw{0.165}}|p{\colw{0.241}}|p{\colw{0.098}}"
    r"|p{\colw{0.075}}|p{\colw{0.135}}|p{\colw{0.135}}|p{\colw{0.150}}|"
)

# 8-col: transport emission (2.0 : 2.0 : 1.3 : 1.5 : 1.5 : 1.5 : 1.5 : 2.1 → /13.4)
_COL_TRANSPORT = (
    r"|p{\colw{0.149}}|p{\colw{0.149}}|p{\colw{0.097}}"
    r"|p{\colw{0.112}}|p{\colw{0.112}}|p{\colw{0.112}}"
    r"|p{\colw{0.112}}|p{\colw{0.157}}|"
)

# 6-col: onsite emission (2.8 : 2.0 : 2.3 : 1.5 : 1.8 : 2.3 → /12.7)
_COL_ONSITE = (
    r"|p{\colw{0.220}}|p{\colw{0.157}}|p{\colw{0.181}}"
    r"|p{\colw{0.118}}|p{\colw{0.142}}|p{\colw{0.181}}|"
)


def _wrap_latex_cell(text, color=None, bold=False):
    cell = escape_latex(str(text))
    if bold:
        cell = r"\textbf{" + cell + r"}"
    wrapped = (
        r"\parbox[t]{\linewidth}{\raggedright\arraybackslash\sloppy"
        r"\seqsplit{" + cell + r"}}"
    )
    if color:
        return r"\cellcolor{" + color + r"}" + wrapped
    return wrapped


def add_input_data(doc, config, data):
    """Section 2: Input Data - all tables matching Word doc."""
    doc.append(NoEscape(r"\newpage"))
    with doc.create(Section("Input data")):
        doc.append(
            "This chapter provides general project information, including "
            "bridge configuration, analysis period, financial data and other "
            "inputs required for conducting life cycle cost assessment."
        )

        # ── 2.1 Bridge geometry ──────────────────────────────────────────
        if config.get(KEY_SHOW_BRIDGE_DESC, True):
            with doc.create(Subsection("Bridge geometry and description")):
                doc.append(
                    "Details of bridge type, span length, number of spans, "
                    "and functional classification."
                )
                doc.add_kv_table(
                    "Bridge description",
                    data.get(KEY_BRIDGE_DESC, {}),
                    key_frac=0.62,
                )

        # ── 2.2 User note (Financial Data) ───────────────────────────────
        if config.get(KEY_SHOW_FINANCIAL, True):
            with doc.create(Subsection("User note")):
                doc.add_kv_table(
                    "Financial Data",
                    data.get(KEY_FINANCIAL, {}),
                )

        # ── 2.3 Construction data ────────────────────────────────────────
        if config.get(KEY_SHOW_CONSTRUCTION, True):

            with doc.create(Subsection("Construction data")):
                doc.append("Material quantities and unit rates.")
                construction = data.get("construction", {})

                # ── Source colour legend ──────────────────────────────────
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(r"\needspace{8\baselineskip}"))
                doc.append(NoEscape(r"\noindent\textbf{Source Legend}"))
                doc.append(NoEscape(r"\vspace{4pt}"))
                doc.append(NoEscape(
                    r"{"
                    r"\footnotesize"
                    r"\begin{longtable}{|p{\colw{0.15}}|p{\colw{0.85}}|}"
                    r"\hline"
                    r"\rowcolor{gray!10}"
                    r"\textbf{Color} & \textbf{Description} \\"
                    r"\hline"
                    r"\cellcolor{white} & Database default (unmodified) \\"
                    r"\hline"
                    r"\cellcolor{srcDbModified} & Database value modified by user \\"
                    r"\hline"
                    r"\cellcolor{srcExcel} & Imported from Excel \\"
                    r"\hline"
                    r"\cellcolor{srcManual} & Manually entered \\"
                    r"\hline"
                    r"\cellcolor{srcCustomDb} & From custom database \\"
                    r"\hline"
                    r"\end{longtable}"
                    r"}"
                ))
                doc.append(NoEscape(r"\vspace{4pt}"))

                cat_table_captions = {
                    "Foundation":     "Construction material quantities and rates for foundation",
                    "Sub Structure":  "Construction material quantities and rates for substructure",
                    "Super Structure":"Construction material quantities and rates for superstructure",
                    "Miscellaneous":  "Construction material quantities and rates for miscellaneous activities",
                }
                header_row = (
                    r"\rowcolor{gray!10}"
                    + r"\centering\textbf{Category} & \textbf{Material}"
                    + r" & \textbf{Rate} & \textbf{Quantity}"
                    + r" & \textbf{Unit} & \textbf{Source} \\"
                )

                # Map meta.source values to LaTeX colour names
                _SOURCE_COLORS = {
                    "db_modified":    "srcDbModified",
                    "excel":          "srcExcel",
                    "manual":         "srcManual",
                    "custom_db":      "srcCustomDb",
                }

                for cat_name, components in construction.items():
                    caption = cat_table_captions.get(
                        cat_name,
                        f"Construction material quantities and rates for {cat_name.lower()}"
                    )
                    doc.append(NoEscape(r"\vspace{4pt}"))

                    rows_tex = ""
                    for comp_name, mat_rows in components.items():
                        row_count = len(mat_rows)
                        # Avoid breaking a category across pages to keep multirow centered
                        doc.append(NoEscape(r"\needspace{" + str(max(2, row_count)) + r"\baselineskip}"))
                        
                        for idx, row_vals in enumerate(mat_rows):
                            mat         = row_vals[0]
                            qty         = row_vals[1]
                            unit        = row_vals[2]
                            rate        = row_vals[3]
                            source      = row_vals[4]
                            meta_source = row_vals[5] if len(row_vals) > 5 else ""
                            
                            latex_color = _SOURCE_COLORS.get(meta_source)
                            color_cmd = r"\cellcolor{" + latex_color + "}" if latex_color else ""
                            
                            if idx == 0:
                                if row_count > 1:
                                    cat_cell = (
                                        r"\cellcolor{white}\multirow{" + str(row_count) + r"}{=}{"
                                        + _wrap_latex_cell(comp_name, "white", bold=True)
                                        + r"}"
                                    )
                                else:
                                    cat_cell = _wrap_latex_cell(comp_name, "white", bold=True)
                            else:
                                cat_cell = "" # Transparent

                            material_cell = _wrap_latex_cell(mat, latex_color)
                            rate_cell = _wrap_latex_cell(rate, latex_color)
                            qty_cell = _wrap_latex_cell(qty, latex_color)
                            unit_cell = _wrap_latex_cell(unit, latex_color)
                            source_cell = _wrap_latex_cell(source, latex_color)

                            cells = [
                                cat_cell,
                                material_cell,
                                rate_cell,
                                qty_cell,
                                unit_cell,
                                source_cell,
                            ]
                            
                            rows_tex += " & ".join(cells)
                            
                            if idx == row_count - 1:
                                rows_tex += r" \\" + "\n" + r"\hline" + "\n"
                            else:
                                rows_tex += r" \\*" + "\n" + r"\cline{2-6}" + "\n"

                    caption_tex = r"\caption{" + escape_latex(caption) + r"}\\" + "\n"
                    longtable_tex = (
                        r"{\footnotesize" + "\n"
                        + r"\begin{longtable}{" + _COL_CONSTRUCTION + r"}" + "\n"
                        + caption_tex
                        + r"\hline" + "\n"
                        + header_row
                        + r"\hline" + "\n"
                        + r"\endfirsthead" + "\n"
                        + r"\hline" + "\n"
                        + header_row
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

        # ── 2.3.1 LCC Assumptions ────────────────────────────────────────
        if config.get(KEY_SHOW_LCC_ASSUMPTIONS, True):
            doc.append(NoEscape(r"\vspace{4pt}"))
            doc.append(NoEscape(r"\needspace{8\baselineskip}"))
            doc.append(NoEscape(
                r"\noindent\captionof{table}{Assumptions for different "
                r"life cycle cost components}"
            ))
            doc.append(NoEscape(r"\vspace{4pt}"))
            with doc.create(Tabular(NoEscape(_COL_LCC_ASSUMPTIONS))) as t:
                t.add_hline()
                t.add_row(["", bold("Assumed percentage"), ""])
                t.add_hline()
                for key, vals in data.get(KEY_LCC_ASSUMPTIONS, {}).items():
                    t.add_row([escape_latex(key),
                               escape_latex(str(vals[0])),
                               escape_latex(str(vals[1]))])
                    t.add_hline()
            doc.append(NoEscape(r"\vspace{4pt}"))

        # ── 2.3.2 Use Stage Details ──────────────────────────────────────
        if config.get(KEY_SHOW_USE_STAGE, True):
            doc.add_kv_table(
                "Details related to duration and interval of use stage activities",
                data.get(KEY_USE_STAGE, {}),
                key_frac=0.69,
            )
