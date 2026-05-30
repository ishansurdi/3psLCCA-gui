import os
from pylatex import (
    Document,
    Package,
    NoEscape,
    Section,
    Subsection,
    Tabular,
)
from pylatex.utils import bold, escape_latex

try:
    from osdag_latex_env import OsdagLatexEnv
except ImportError:
    OsdagLatexEnv = None

class LCCAReportBase(Document):
    try:
        osdag_latex = OsdagLatexEnv() if OsdagLatexEnv else None
    except Exception:
        print("Warning: Failed to initialize osdag_latex_env. Falling back to system pdflatex.")
        osdag_latex = None

    LATEX_EXEC = str(getattr(osdag_latex, "pdflatex", "pdflatex"))

    def __init__(self):
        geometry = {
            "tmargin": "1in",
            "bmargin": "1in",
            "lmargin": "1in",
            "rmargin": "1in",
        }
        super().__init__(geometry_options=geometry, document_options=["12pt", "a4paper"])

        # Packages
        self.packages.append(Package("graphicx"))
        self.packages.append(Package("tikz"))
        self.packages.append(Package("tabularx"))
        self.packages.append(Package("float"))
        self.packages.append(Package("caption"))
        self.packages.append(Package("needspace"))
        self.packages.append(Package("longtable"))
        self.packages.append(Package("array"))
        self.packages.append(Package("amsmath"))
        self.packages.append(Package("xcolor", options=["table"]))
        self.packages.append(Package("colortbl"))
        self.packages.append(Package("newtxtext"))
        self.packages.append(Package("newtxmath"))
        self.packages.append(Package("multirow"))
        self.packages.append(Package("seqsplit"))
        self.packages.append(Package("enumitem"))
        self.packages.append(
             
            
            Package(
                "hyperref",
                options=["colorlinks=true", "linkcolor=black", "urlcolor=blue"],
            )
        )
        

        self.preamble.append(NoEscape(r"""
\renewcommand{\arraystretch}{1.2}
\setlength{\tabcolsep}{5pt}
\pagestyle{plain}
\numberwithin{table}{section}
\numberwithin{figure}{section}
\renewcommand{\thetable}{\thesection-\arabic{table}}
\renewcommand{\thefigure}{\thesection-\arabic{figure}}
% \colw{fraction}: column width as a fraction of \linewidth, accounting for
% tabcolsep and arrayrulewidth so columns summing to 1.0 fill exactly one line.
\newcommand{\colw}[1]{\dimexpr #1\linewidth - 2\tabcolsep - \arrayrulewidth\relax}
% \fixedcolw{fraction}: column width as a fraction of \textwidth, useful for nested tables.
\newcommand{\fixedcolw}[1]{\dimexpr #1\textwidth - 2\tabcolsep - \arrayrulewidth\relax}
% Make tabularx X columns behave like p{} (top-aligned, ragged-right)
\renewcommand{\tabularxcolumn}[1]{p{#1}}
% ── Source-tracking row colours ──────────────────────────────────────────
\definecolor{srcDbModified}{HTML}{E6CCB2}   % light brown - DB item modified by user
\definecolor{srcExcel}{HTML}{90EE90}        % light green - imported from Excel (previous green)
\definecolor{srcManual}{HTML}{FFF9C4}       % light yellow- manually entered
\definecolor{srcCustomDb}{HTML}{E8DAEF}     % light purple- from custom database

\DeclareUnicodeCharacter{20B9}{Rs.}
\DeclareUnicodeCharacter{2082}{\textsubscript{2}}
"""))

    def add_kv_table(self, caption, data, key_frac=0.50, need_lines=6):
        """2-column key-value table spanning full text width.
        key_frac: fraction of linewidth for the key column (default 0.50).
        The value column gets the remaining fraction.
        """
        if not data:
            return
        self.append(NoEscape(r"\vspace{4pt}"))
        self.append(NoEscape(r"\needspace{" + str(need_lines) + r"\baselineskip}"))
        self.append(NoEscape(r"\noindent\captionof{table}{" + escape_latex(caption) + r"}"))
        self.append(NoEscape(r"\vspace{4pt}"))
        key_col = rf"\colw{{{key_frac}}}"
        self.append(NoEscape(
            r"\begin{tabularx}{\linewidth}{|p{" + key_col + r"}|X|}"
            r"\hline"
        ))
        for key, val in data.items():
            self.append(NoEscape(
                escape_latex(str(key)) + r" & " + escape_latex(str(val)) + r"\\ \hline"
            ))
        self.append(NoEscape(r"\end{tabularx}"))
        self.append(NoEscape(r"\vspace{4pt}"))

    def add_multi_table(self, caption, headers, data, col_spec, need_lines=6):
        """Multi-column table. col_spec should use \\colw{f} fractions."""
        self.append(NoEscape(r"\vspace{4pt}"))
        self.append(NoEscape(r"\needspace{" + str(need_lines) + r"\baselineskip}"))
        self.append(NoEscape(r"\noindent\captionof{table}{" + escape_latex(caption) + r"}"))
        self.append(NoEscape(r"\vspace{4pt}"))
        with self.create(Tabular(col_spec)) as t:
            t.add_hline()
            t.add_row([bold(h) for h in headers])
            t.add_hline()
            for row in data:
                t.add_row([escape_latex(str(c)) for c in row])
                t.add_hline()
        self.append(NoEscape(r"\vspace{4pt}"))