# code_to_latex - Rules

**Only use `pylatex` or `pandas.DataFrame.to_latex()` to generate LaTeX code.**

- No manual string building (`f"..."`, `"\n".join(...)`, hardcoded `\begin{...}` strings, etc.)
- No custom escaping helpers - let pylatex or pandas handle escaping
- Use `pylatex` when the table has mixed-structure rows (e.g. section headers spanning columns)
- Use `pandas.to_latex()` when the table is flat (uniform columns every row)
- Numeric value columns must be right-aligned - use `r` column spec, not `l`
- Always use `booktabs` rules (`\toprule`, `\midrule`, `\bottomrule`) - never `\hline`
- Every table must have a `\caption` and a `\label{tab:...}`
- Units go in the column header or field label, not in individual value cells
- Missing/empty values render as `\textemdash`, not blank, zero, or `N/A`
- Tables go inside a `table` float with `\centering` - never bare `tabular` in the output
- Every component latex file must expose a single `<component>_to_latex(controller)` function and nothing else
- Each component has its own `.py` file so output can be individually controlled - do not try to fully automate or over-generalize; `common_code.py` only exists for shared low-level utilities, not to eliminate per-component decisions
- To register a new component in the Dev > LaTeX menu, add one entry to `_LATEX_ENTRIES` in `devmode.py` - do not duplicate the save/wrap logic
- src\three_ps_lcca_gui\gui\devmode.py

## Decimal precision
- Never hardcode decimal place counts — import `DECIMAL_PLACES_FOR_LATEX` (general values) and `DECIMAL_PLACES_FOR_LATEX_RATIO` (ratio/index values) from `SETTINGS.py`
- `src\three_ps_lcca_gui\code_to_latex\SETTINGS.py`

## Font size
- Never hardcode font size declarations (`\small`, `\footnotesize`, etc.) in component files — the document-level font size is set via `LATEX_FONT_SIZE` in `SETTINGS.py` and applied once by devmode after `\begin{document}`
- Exception: element-level annotations (e.g. legend footnotes, "continued on next page" footers) may use `\footnotesize` locally since they are intentionally smaller than body text

## Units
- Never hardcode unit display strings from raw chunk data — use `UNIT_DISPLAY` from `src\three_ps_lcca_gui\gui\components\utils\definitions.py` to resolve unit codes (e.g. `"m3"` → `"m³"`)
- `UNIT_DISPLAY.get(code, code)` — falls back to the raw code if unknown
- Only applies where unit codes come directly from chunk data (e.g. structure work items); `FieldDef.unit` strings are already human-readable and do not need resolving

## Currency
- Never hardcode currency strings (e.g. `"INR"`) — call `get_currency()` from `src\three_ps_lcca_gui\gui\components\utils\common_requested_data.py` at function call time, not at module level