from pylatex import LongTable, MultiColumn, NoEscape
from pylatex.utils import bold, italic, escape_latex
from ..gui.components.utils.common_requested_data import (
    get_str_foundation, get_str_sub_structure, get_str_super_structure, get_str_misc,
    get_currency,
)
from ..gui.components.utils.definitions import UNIT_DISPLAY
from .SETTINGS import DECIMAL_PLACES_FOR_LATEX

_EMDASH     = NoEscape(r"\textemdash")
_MIDRULE    = NoEscape(r"\midrule")
_BOTTOMRULE = NoEscape(r"\bottomrule")
_N_COLS     = 6
_COL_SPEC   = "p{4cm}rp{1.2cm}rp{2.5cm}r"

_SOURCE_MARK = {
    "db":             "",
    "manual":         r"$^{\#}$",
    "db_modified":    r"$^{\S}$",
    "excel":          r"$^{\dagger}$",
    "excel_modified": r"$^{\ddagger}$",
}


def _legend(currency: str) -> NoEscape:
    cur = escape_latex(currency)
    return NoEscape(
        r"\par\smallskip\footnotesize"
        rf" All rates and totals in {cur}.\quad"
        r"\textemdash\,Database value (default);\quad"
        r"$^{\#}$\,Manually entered;\quad"
        r"$^{\S}$\,Modified from database;\quad"
        r"$^{\dagger}$\,Imported from Excel;\quad"
        r"$^{\ddagger}$\,Imported from Excel and modified"
    )


def _fmt(val):
    if val is None:
        return _EMDASH
    return f"{val:.{DECIMAL_PLACES_FOR_LATEX}f}"


def _mat_cell(name: str, source: str):
    mark = _SOURCE_MARK.get(source, "")
    if not name:
        return _EMDASH
    return NoEscape(escape_latex(name) + mark)


def _structure_table(chunk: dict, caption: str, label: str, currency: str) -> str:
    headers = ["Material", "Quantity", "Unit", "Rate/Unit", "Rate Source", f"Total ({currency})"]

    table = LongTable(_COL_SPEC)

    # ── first head ───────────────────────────────────────────────────────────
    # \caption{}\label{}\\ must be a single NoEscape line before the header row
    table.append(NoEscape(
        r"\caption{" + escape_latex(caption) + r"}"
        r"\label{" + label + r"}\\"
    ))
    table.append(_MIDRULE)
    table.add_row([bold(h) for h in headers])
    table.append(_MIDRULE)
    table.append(NoEscape(r"\endfirsthead"))

    # ── continued head ───────────────────────────────────────────────────────
    table.add_row([MultiColumn(_N_COLS, align="l",
                               data=italic("Continued from previous page"))])
    table.append(_MIDRULE)
    table.add_row([bold(h) for h in headers])
    table.append(_MIDRULE)
    table.end_table_header()

    # ── mid-page foot ────────────────────────────────────────────────────────
    table.append(_MIDRULE)
    table.add_row([MultiColumn(_N_COLS, align="r",
                               data=italic("Continued on next page"))])
    table.end_table_footer()

    # ── last foot ────────────────────────────────────────────────────────────
    table.append(_BOTTOMRULE)
    table.end_table_last_footer()

    # ── data rows ────────────────────────────────────────────────────────────
    first = True
    for component_name, items in chunk.items():
        if not first:
            table.append(_MIDRULE)
        first = False

        table.add_row([MultiColumn(_N_COLS, align="l", data=bold(component_name))])
        table.append(_MIDRULE)

        for item in items:
            if item.get("state", {}).get("in_trash"):
                continue
            v      = item.get("values", {})
            source = item.get("meta", {}).get("source", "db")
            qty    = v.get("quantity")
            rate   = v.get("rate")
            total  = (qty * rate) if (qty is not None and rate is not None) else None

            table.add_row([
                _mat_cell(v.get("material_name", ""), source),
                _fmt(qty),
                UNIT_DISPLAY.get(v.get("unit", ""), v.get("unit")) or _EMDASH,
                _fmt(rate),
                v.get("rate_source") or _EMDASH,
                _fmt(total),
            ])

    return table.dumps() + "\n" + str(_legend(currency))


def structure_work_data_to_latex(controller=None) -> str:
    currency = get_currency()
    return "\n\n".join([
        _structure_table(get_str_foundation(),      "Structure Work Data: Foundation",      "tab:str_foundation",      currency),
        _structure_table(get_str_sub_structure(),   "Structure Work Data: Sub-Structure",   "tab:str_sub_structure",   currency),
        _structure_table(get_str_super_structure(), "Structure Work Data: Super Structure", "tab:str_super_structure", currency),
        _structure_table(get_str_misc(),            "Structure Work Data: Miscellaneous",   "tab:str_misc",            currency),
    ])