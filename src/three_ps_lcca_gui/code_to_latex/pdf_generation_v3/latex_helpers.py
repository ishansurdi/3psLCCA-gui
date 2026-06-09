from __future__ import annotations

from pylatex.utils import escape_latex

from ..SETTINGS import LATEX_FONT_SIZE


EMDASH = r"\textemdash"

V3_PREAMBLE = [
    r"\documentclass[12pt,a4paper]{article}",
    r"\usepackage[utf8]{inputenc}",
    r"\usepackage{booktabs}",
    r"\usepackage{array}",
    r"\usepackage{longtable}",
    r"\usepackage{graphicx}",
    r"\usepackage{caption}",
    r"\usepackage{float}",
    r"\usepackage{pdflscape}",
    r"\usepackage{adjustbox}",
    r"\usepackage{etoolbox}",
    r"\usepackage{amsmath}",
    r"\usepackage{xcolor}",
    r"\usepackage{tocloft}",
    r"\usepackage{titlesec}",
    r"\usepackage[a4paper, top=2.5cm, bottom=2.5cm, left=2.5cm, right=2.5cm]{geometry}",
    r"\usepackage[hidelinks,hypertexnames=false]{hyperref}",
    r"\DeclareUnicodeCharacter{20B9}{Rs.}",
    r"\DeclareUnicodeCharacter{2082}{\textsubscript{2}}",
    r"\DeclareUnicodeCharacter{2013}{--}",
    r"\DeclareUnicodeCharacter{2014}{--}",
    r"\setlength{\tabcolsep}{4pt}",
    r"\renewcommand{\arraystretch}{1.18}",
    r"\setlength{\LTleft}{0pt}",
    r"\setlength{\LTright}{0pt}",
    r"\setlength{\LTcapwidth}{\textwidth}",
    r"\renewcommand{\contentsname}{Table of Contents}",
    r"\renewcommand{\listtablename}{List of Tables}",
    r"\renewcommand{\listfigurename}{List of Figures}",
    r"\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}}",
    r"\renewcommand{\cftsubsecleader}{\cftdotfill{\cftdotsep}}",
    r"\titleformat{\section}{\Large\bfseries\color{blue!55!black}}{\thesection}{0.75em}{}",
    r"\titleformat{\subsection}{\large\bfseries\color{blue!55!black}}{\thesubsection}{0.75em}{}",
    r"\BeforeBeginEnvironment{tabular}{\begin{adjustbox}{max width=\linewidth}}",
    r"\AfterEndEnvironment{tabular}{\end{adjustbox}}",
    r"\sloppy",
]


def build_report_v3_document(body: str) -> str:
    """Wrap report body in the V3 LaTeX document shell."""
    return "\n".join([
        *V3_PREAMBLE,
        r"\begin{document}",
        LATEX_FONT_SIZE,
        body,
        r"\end{document}",
    ])


def title_page(project_name: str) -> str:
    safe_project_name = escape_latex(project_name or "Unnamed Project")
    return "\n".join([
        r"\begin{titlepage}",
        r"\begin{flushright}",
        r"\IfFileExists{../../gui/assets/logo/3pslcca_header.png}{\includegraphics[width=0.38\linewidth]{../../gui/assets/logo/3pslcca_header.png}}{}",
        r"\end{flushright}",
        r"\vspace*{2cm}",
        r"\noindent{\color{blue!55!black}\rule{\linewidth}{1.2pt}}",
        r"\vspace{0.8cm}",
        r"\begin{flushright}",
        r"{\Huge\bfseries Software Generated Report\par}",
        r"\vspace{0.45cm}",
        r"{\LARGE Life Cycle Cost Assessment\par}",
        r"\vspace{0.8cm}",
        r"{\Large " + safe_project_name + r"\par}",
        r"\end{flushright}",
        r"\vspace{0.8cm}",
        r"\noindent{\color{blue!55!black}\rule{\linewidth}{0.8pt}}",
        r"\vfill",
        r"\begin{flushright}",
        r"{\large Generated from code-to-LaTeX exporters\par}",
        r"\end{flushright}",
        r"\end{titlepage}",
    ])


def front_matter() -> str:
    """TOC, list of tables, and list of figures."""
    return "\n".join([
        r"\clearpage",
        r"\pagenumbering{roman}",
        r"\tableofcontents",
        r"\clearpage",
        r"\addcontentsline{toc}{section}{List of Tables}",
        r"\listoftables",
        r"\clearpage",
        r"\addcontentsline{toc}{section}{List of Figures}",
        r"\listoffigures",
        r"\clearpage",
        r"\pagenumbering{arabic}",
    ])


def section(title: str) -> str:
    return r"\section{" + escape_latex(title) + r"}"


def subsection(title: str) -> str:
    return r"\subsection{" + escape_latex(title) + r"}"


def paragraph(text: str) -> str:
    return r"\par\medskip " + escape_latex(text) + r"\par\medskip"


def clearpage() -> str:
    return r"\clearpage"


def appendix_counter(letter: str) -> str:
    section_number = ord(letter.upper()) - ord("A") + 1
    lines = []
    if letter.upper() == "A":
        lines.append(r"\appendix")
    lines.extend([
        r"\setcounter{section}{" + str(section_number) + r"}",
        r"\setcounter{table}{0}",
        r"\setcounter{figure}{0}",
    ])
    return "\n".join(lines)


def format_value(value, decimals: int | None = None) -> str:
    if value in (None, ""):
        return EMDASH
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if decimals is not None:
        return f"{number:,.{decimals}f}"
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.2f}".rstrip("0").rstrip(".")


def simple_table(
    caption: str,
    label: str,
    headers: list[str],
    rows: list[list],
    col_spec: str,
) -> str:
    if not rows:
        rows = [[EMDASH for _ in headers]]

    header = " & ".join(r"\textbf{" + escape_latex(h) + "}" for h in headers) + r" \\"
    body = [
        " & ".join(_cell(c) for c in row) + r" \\"
        for row in rows
    ]

    return "\n".join([
        r"\begin{longtable}{" + col_spec + r"}",
        r"\caption{" + escape_latex(caption) + r"}\label{" + label + r"}\\",
        r"\toprule",
        header,
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        header,
        r"\midrule",
        r"\endhead",
        r"\midrule",
        r"\multicolumn{" + str(len(headers)) + r"}{r}{\footnotesize\textit{continued on next page}} \\",
        r"\endfoot",
        r"\bottomrule",
        r"\endlastfoot",
        *body,
        r"\end{longtable}",
    ])


def wide_block(latex: str, size: str = r"\scriptsize") -> str:
    if not latex:
        return ""
    latex = latex.replace(r"\begin{landscape}", "").replace(r"\end{landscape}", "")
    return "\n".join([
        r"\begingroup",
        size,
        r"\centering",
        r"\setlength{\tabcolsep}{2pt}",
        r"\setlength{\LTleft}{\fill}",
        r"\setlength{\LTright}{\fill}",
        latex,
        r"\normalsize",
        r"\endgroup",
    ])


def _cell(value) -> str:
    if value in (None, ""):
        return EMDASH
    if value == EMDASH:
        return EMDASH
    return escape_latex(str(value))
