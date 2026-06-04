# code_to_latex — Rules

**Only use `pylatex` or `pandas.DataFrame.to_latex()` to generate LaTeX code.**

- No manual string building (`f"..."`, `"\n".join(...)`, hardcoded `\begin{...}` strings, etc.)
- No custom escaping helpers — let pylatex or pandas handle escaping
- Use `pylatex` when the table has mixed-structure rows (e.g. section headers spanning columns)
- Use `pandas.to_latex()` when the table is flat (uniform columns every row)
- Numeric value columns must be right-aligned — use `r` column spec, not `l`
- Always use `booktabs` rules (`\toprule`, `\midrule`, `\bottomrule`) — never `\hline`
- Every table must have a `\caption` and a `\label{tab:...}`
- Units go in the column header or field label, not in individual value cells
- Missing/empty values render as `\textemdash`, not blank, zero, or `N/A`
- Tables go inside a `table` float with `\centering` — never bare `tabular` in the output
- Every component latex file must expose a single `<component>_to_latex(controller)` function and nothing else
- Each component has its own `.py` file so output can be individually controlled — do not try to fully automate or over-generalize; `common_code.py` only exists for shared low-level utilities, not to eliminate per-component decisions
- To register a new component in the Dev > LaTeX menu, add one entry to `_LATEX_ENTRIES` in `devmode.py` — do not duplicate the save/wrap logic
- src\three_ps_lcca_gui\gui\devmode.py