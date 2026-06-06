from collections import defaultdict

from pylatex import LongTable, MultiColumn, NoEscape
from pylatex.utils import bold, escape_latex

from ..gui.components.utils.common_requested_data import get_chunk
from ..gui.components.utils.definitions import STRUCTURE_CHUNKS, UNIT_DISPLAY
from .SETTINGS import DECIMAL_PLACES_FOR_LATEX
from .html_to_latex import format_remarks_latex

_EMDASH = r"\textemdash"

_INC_COLS    = 7
_INC_SPEC    = "p{3.5cm}rp{1cm}rrp{1.5cm}r"
_INC_HEADERS = [
    "Material", "Quantity", "Unit",
    "Conversion Factor", "Emission Factor",
    NoEscape(r"EF Unit"),
    NoEscape(r"Total (kgCO\textsubscript{2}e)"),
]

_EXC_COLS    = 1
_EXC_SPEC    = "p{10cm}"
_EXC_HEADERS = ["Material"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt(val) -> str:
    try:
        return f"{float(val):,.{DECIMAL_PLACES_FOR_LATEX}f}"
    except (TypeError, ValueError):
        return _EMDASH


def _collect():
    included = defaultdict(list)
    excluded = defaultdict(list)

    for chunk_id, category in STRUCTURE_CHUNKS:
        for comp_name, items in get_chunk(chunk_id).items():
            for item in items:
                if item.get("state", {}).get("in_trash", False):
                    continue
                values = item.get("values", {})
                state  = item.get("state", {})
                key    = (category, comp_name)

                qty    = float(values.get("quantity",          0) or 0)
                cf     = float(values.get("conversion_factor", 1) or 1)
                ef     = float(values.get("carbon_emission",   0) or 0)
                unit   = UNIT_DISPLAY.get(values.get("unit", ""), values.get("unit", ""))
                ef_unit = values.get("carbon_unit", "")

                if state.get("included_in_carbon_emission") is True:
                    included[key].append({
                        "material": values.get("material_name", ""),
                        "qty": qty, "unit": unit,
                        "cf": cf, "ef": ef,
                        "ef_unit": ef_unit,
                        "total": qty * cf * ef,
                    })
                else:
                    excluded[key].append(values.get("material_name", ""))

    return included, excluded


def _longtable(col_spec, n_cols, caption, label, headers, sections) -> str:
    table = LongTable(col_spec)

    table.append(NoEscape(
        rf"\caption{{{escape_latex(caption)}}} \label{{{label}}} \\"
    ))
    table.append(NoEscape(r"\toprule"))
    table.add_row(headers)
    table.append(NoEscape(r"\midrule"))
    table.append(NoEscape(r"\endhead"))

    table.append(NoEscape(r"\midrule"))
    table.append(NoEscape(
        rf"\multicolumn{{{n_cols}}}{{r}}{{\footnotesize\textit{{continued on next page}}}} \\"
    ))
    table.append(NoEscape(r"\endfoot"))

    table.append(NoEscape(r"\bottomrule"))
    table.append(NoEscape(r"\endlastfoot"))

    first = True
    for header_text, rows in sections:
        if not rows:
            continue
        if not first:
            table.append(NoEscape(r"\midrule"))
        first = False

        table.append(NoEscape(
            MultiColumn(n_cols, align="l",
                        data=bold(escape_latex(header_text))).dumps() + r" \\"
        ))
        table.append(NoEscape(r"\midrule"))

        for row in rows:
            table.add_row(row)

    return table.dumps()


# ── Public table builders ─────────────────────────────────────────────────────

def _get_included_table(included: dict) -> str:
    if not included:
        return ""

    sections = []
    for (category, comp_name), rows in included.items():
        cells = [
            [
                escape_latex(r["material"]),
                _fmt(r["qty"]),
                escape_latex(r["unit"]),
                _fmt(r["cf"]),
                _fmt(r["ef"]),
                escape_latex(r["ef_unit"]),
                _fmt(r["total"]),
            ]
            for r in rows
        ]
        sections.append((f"{category} — {comp_name}", cells))

    return _longtable(
        _INC_SPEC, _INC_COLS,
        "Materials Included in Carbon Emissions Calculation",
        "tab:material_emissions_included",
        _INC_HEADERS, sections,
    )


def _get_excluded_table(excluded: dict) -> str:
    if not excluded:
        return ""

    sections = []
    for (category, comp_name), names in excluded.items():
        sections.append(
            (f"{category} — {comp_name}",
             [[escape_latex(n)] for n in names])
        )

    return _longtable(
        _EXC_SPEC, _EXC_COLS,
        "Materials Excluded from Carbon Emissions Calculation",
        "tab:material_emissions_excluded",
        _EXC_HEADERS, sections,
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def material_emissions_to_latex(controller=None) -> str:
    included, excluded = _collect()
    parts = [_get_included_table(included), _get_excluded_table(excluded)]
    out = "\n\n".join(t for t in parts if t)
    
    # Material emissions remarks are stored in 'material_emissions_data'
    data = get_chunk("material_emissions_data")
    remarks = format_remarks_latex(data)
    if remarks:
        out += "\n\n" + remarks
    return out
