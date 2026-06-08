from pylatex.utils import escape_latex

from ..SETTINGS import LATEX_FONT_SIZE


V3_PREAMBLE = [
    r"\documentclass[12pt,a4paper]{article}",
    r"\usepackage[utf8]{inputenc}",
    r"\usepackage{booktabs}",
    r"\usepackage{array}",
    r"\usepackage{amsmath}",
    r"\usepackage{xcolor}",
    r"\usepackage{enumitem}",
    r"\usepackage{longtable}",
    r"\usepackage{graphicx}",
    r"\usepackage{caption}",
    r"\usepackage{float}",
    r"\usepackage{pdflscape}",
    r"\usepackage{adjustbox}",
    r"\usepackage{etoolbox}",
    r"\usepackage{chngcntr}",
    r"\usepackage[a4paper, top=2.5cm, bottom=2.5cm, left=2.5cm, right=2.5cm]{geometry}",
    r"\usepackage[hidelinks]{hyperref}",
    r"\DeclareUnicodeCharacter{2082}{\textsubscript{2}}",
    r"\counterwithin{table}{section}",
    r"\counterwithin{figure}{section}",
    r"\renewcommand{\thetable}{\thesection-\arabic{table}}",
    r"\renewcommand{\thefigure}{\thesection-\arabic{figure}}",
    r"\BeforeBeginEnvironment{tabular}{\begin{adjustbox}{max width=\linewidth}}",
    r"\AfterEndEnvironment{tabular}{\end{adjustbox}}",
    r"\setlength{\tabcolsep}{4pt}",
    r"\renewcommand{\arraystretch}{1.2}",
    r"\setlength{\LTleft}{0pt}",
    r"\setlength{\LTright}{0pt}",
    r"\setlength{\LTcapwidth}{\textwidth}",
]


def build_report_v3_document(body: str) -> str:
    """Return a complete LaTeX document for the V3 PDF report."""
    return "\n".join([
        *V3_PREAMBLE,
        r"\begin{document}",
        LATEX_FONT_SIZE,
        body,
        r"\end{document}",
    ])


def title_page(project_name: str, report_title: str = "Life Cycle Cost Assessment Report") -> str:
    safe_project_name = escape_latex(project_name or "Unnamed Project")
    safe_report_title = escape_latex(report_title)

    return "\n".join([
        r"\begin{titlepage}",
        r"\centering",
        r"\vspace*{3cm}",
        r"{\LARGE\bfseries " + safe_report_title + r"\par}",
        r"\vspace{1.5cm}",
        r"{\Large " + safe_project_name + r"\par}",
        r"\vfill",
        r"{\large Software Generated Report\par}",
        r"\end{titlepage}",
    ])


def front_matter() -> str:
    """TOC, list of tables, and list of figures for the V3 report."""
    return "\n".join([
        r"\renewcommand{\thetable}{\thesection-\arabic{table}}",
        r"\renewcommand{\thefigure}{\thesection-\arabic{figure}}",
        r"\makeatletter",
        r"\@addtoreset{table}{section}",
        r"\@addtoreset{figure}{section}",
        r"\makeatother",
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


def subsubsection(title: str) -> str:
    return r"\subsubsection{" + escape_latex(title) + r"}"


def paragraph(text: str) -> str:
    return r"\par\medskip " + escape_latex(text) + r"\par\medskip"


def clearpage() -> str:
    return r"\clearpage"


def unnumbered_toc_section(title: str) -> str:
    safe_title = escape_latex(title)
    return "\n".join([
        r"\clearpage",
        r"\section*{" + safe_title + r"}",
        r"\addcontentsline{toc}{section}{" + safe_title + r"}",
    ])


def placeholder_figure(caption: str) -> str:
    safe_caption = escape_latex(caption)
    return "\n".join([
        r"\begin{figure}[h!]",
        r"\centering",
        r"\fbox{",
        r"\begin{minipage}[c][4cm][c]{0.82\linewidth}",
        r"\centering",
        r"\textit{" + safe_caption + r"}",
        r"\end{minipage}",
        r"}",
        r"\caption{" + safe_caption + r"}",
        r"\end{figure}",
    ])


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
