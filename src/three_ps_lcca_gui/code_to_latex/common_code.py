from pylatex import Table, Tabular, MultiColumn, NoEscape
from pylatex.utils import bold
from ..gui.components.utils.form_builder.form_definitions import Section, FieldDef


def fields_to_latex(fields: list, data: dict, caption: str, label: str) -> str:
    """Build a pylatex table from a list of Section/FieldDef entries and a data dict.

    Columns: Title | Value | Unit
    Args:
        fields:  FIELDS list (mix of Section and FieldDef)
        data:    chunk dict {key: value}
        caption: table caption string
        label:   LaTeX label string, e.g. "tab:bridge_data"
    """
    tabular = Tabular("lll")
    tabular.append(NoEscape(r"\toprule"))

    first_section = True
    for entry in fields:
        if isinstance(entry, Section):
            if not first_section:
                tabular.append(NoEscape(r"\midrule"))
            first_section = False
            tabular.append(NoEscape(MultiColumn(3, align="l", data=bold(entry.title)).dumps() + r" \\"))
            tabular.append(NoEscape(r"\midrule"))
        elif isinstance(entry, FieldDef):
            raw = data.get(entry.key, "")
            if raw in ("", None):
                value = NoEscape(r"\textemdash")
            elif isinstance(raw, (int, float)):
                value = MultiColumn(1, align="r", data=str(raw))
            else:
                value = str(raw)
            tabular.add_row(entry.title, value, entry.unit or "")

    tabular.append(NoEscape(r"\bottomrule"))

    table = Table(position="h!")
    table.append(NoEscape(r"\centering"))
    table.add_caption(caption)
    table.append(NoEscape(rf"\label{{{label}}}"))
    table.append(tabular)

    return table.dumps()
