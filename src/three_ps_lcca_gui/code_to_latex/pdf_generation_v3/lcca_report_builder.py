from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Callable
import shutil
import tempfile

from pylatex.utils import escape_latex

from three_ps_lcca_gui.report.constants import (
    KEY_PLOT_PILLAR_BARS,
    KEY_PLOT_PILLAR_DONUT,
    KEY_PLOT_STAGE_BARS,
    KEY_PLOT_SUSTAINABILITY_MATRIX,
)

from ..bridge_data_latex import bridge_data_to_latex
from ..financial_data_latex import financial_data_to_latex
from ..maintenance_data_latex import maintenance_data_to_latex
from ..structure_work_data_latex import structure_work_data_to_latex
from ..traffic_and_road_data_latex.get_all_data import (
    diversion_emissions_to_latex,
    peak_hour_distribution_to_latex,
    traffic_fields_to_latex,
    vehicle_data_to_latex,
    wpi_tables_to_latex,
)
from ..material_emissions_latex import material_emissions_to_latex
from ..transport_emissions_latex import transport_emissions_to_latex
from ..machinery_emissions_latex import machinery_emissions_to_latex
from ..recycling_latex import recycling_to_latex
from ..results_latex import results_to_latex
from .appendix_A_content import APPENDIX_A_LATEX
from .latex_helpers import (
    build_report_v3_document,
    clearpage,
    front_matter,
    section,
    subsection,
    title_page,
    wide_block,
)
from .sections.appendices import appendices_to_latex
from .sections.introduction import introduction_to_latex
from ..social_cost_data_latex import social_cost_data_to_latex


def _project_name(controller=None) -> str:
    for method_name in ("get_fresh_chunk", "get_chunk", "fetch_chunk"):
        method = getattr(controller, method_name, None)
        if callable(method):
            try:
                data = method("general_info") or {}
                if data.get("project_name"):
                    return str(data["project_name"])
            except Exception:
                pass
    return "Unnamed Project"


def _call_exporter(controller, exporter: Callable, title: str) -> str:
    try:
        latex = exporter(controller)
    except Exception as exc:
        print(f"[structured_code_to_latex_report] {title} failed: {exc}")
        return ""
    return latex if latex and latex.strip() else ""


def _chunk(controller, name: str) -> dict:
    for method_name in ("get_fresh_chunk", "get_chunk", "fetch_chunk"):
        method = getattr(controller, method_name, None)
        if callable(method):
            try:
                return method(name) or {}
            except Exception:
                pass
    return {}





def _part(controller, title: str, exporter: Callable, wide: bool = False, size: str = r"\scriptsize") -> str:
    latex = _call_exporter(controller, exporter, title)
    latex = latex.replace(r"\begin{table}[h!]", r"\begin{table}[H]")
    latex = latex.replace(r"\begin{table}[htbp]", r"\begin{table}[H]")
    if wide:
        latex = wide_block(latex, size=size)
    return latex


def _sum_result_numbers(value, key: str = "") -> float:
    if isinstance(value, (int, float)):
        number = float(value)
        return -number if key == "total_scrap_value" else number
    if isinstance(value, dict):
        return sum(_sum_result_numbers(v, k) for k, v in value.items())
    if isinstance(value, list):
        return sum(_sum_result_numbers(v) for v in value)
    return 0.0


def _summary_replacements(controller) -> tuple[str, str, str, str]:
    cache = _valid_result_cache(controller)
    results = cache.get("results", {}) if isinstance(cache, dict) else {}
    if not results:
        return "", "", "", ""

    stages = [
        ("initial_stage", "Initial stage"),
        ("use_stage", "Use stage"),
        ("reconstruction", "Reconstruction"),
        ("end_of_life", "End-of-life"),
    ]
    pillars = [
        ("economic", "Economic"),
        ("environmental", "Environmental"),
        ("social", "Social"),
    ]

    stage_totals = {
        label: _sum_result_numbers(results.get(key, {}))
        for key, label in stages
        if results.get(key)
    }
    pillar_totals = {
        label: sum(_sum_result_numbers(results.get(stage_key, {}).get(key, {})) for stage_key, _ in stages)
        for key, label in pillars
    }
    grand_total = sum(stage_totals.values())
    if not grand_total:
        return "", "", "", ""

    stage_label, stage_value = max(stage_totals.items(), key=lambda item: item[1])
    pillar_label, pillar_value = max(pillar_totals.items(), key=lambda item: item[1])
    return (
        escape_latex(stage_label),
        f"{(stage_value / grand_total) * 100:.2f}",
        escape_latex(pillar_label),
        f"{(pillar_value / grand_total) * 100:.2f}",
    )


def _summary_from_v3_content(controller=None) -> str:
    marker = "Appendix A: Assumptions"
    marker_pos = APPENDIX_A_LATEX.find(marker)
    if marker_pos == -1:
        return ""
    end = APPENDIX_A_LATEX.rfind(r"\section*", 0, marker_pos)
    if end == -1:
        return ""
    content = APPENDIX_A_LATEX[:end]
    remove_from = content.find(r"\begin{itemize}")
    if remove_from != -1:
        content = content[:remove_from]
    content = content.replace(r"\clearpage", r"\clearpage")
    content = content.replace(
        r"\section*{\fontsize{14pt}{16pt}\selectfont\bfseries Summary and Conclusions}",
        r"\section{Summary and conclusions}",
    )
    content = content.replace(
        r"\addcontentsline{toc}{section}{Summary and Conclusions}",
        "",
    )
    stage_label, stage_pct, pillar_label, pillar_pct = _summary_replacements(controller)
    if stage_label:
        content = content.replace(
            r"The most contributing stage of the life cycle is \underline{\hspace{3cm}} "
            "\n"
            r"contributing to around \underline{\hspace{2cm}}\% of the total life cycle cost.",
            rf"The most contributing stage of the life cycle is \textbf{{{stage_label}}} "
            rf"contributing to around \textbf{{{stage_pct}\%}} of the total life cycle cost.",
        )
    if pillar_label:
        content = content.replace(
            r"The most contributing pillar is \underline{\hspace{3cm}} contributing to around \underline{\hspace{2cm}}\% of the total life cycle cost.",
            rf"The most contributing pillar is \textbf{{{pillar_label}}} contributing to around \textbf{{{pillar_pct}\%}} of the total life cycle cost.",
        )
    return content


def _fit_appendix_b_tables(latex: str) -> str:
    marker = "Appendix B: Calculation"
    marker_pos = latex.find(marker)
    if marker_pos == -1:
        return latex

    prefix = latex[:marker_pos]
    appendix_b = latex[marker_pos:]
    appendix_b = appendix_b.replace(
        r"{\fontsize{9pt}{11pt}\selectfont",
        r"{\fontsize{7pt}{8.5pt}\selectfont",
    )
    appendix_b = appendix_b.replace(
        r"\everymath{\fontsize{9pt}{11pt}\selectfont}",
        r"\everymath{\fontsize{7pt}{8.5pt}\selectfont}",
    )
    appendix_b = appendix_b.replace(
        r"\everydisplay{\fontsize{9pt}{11pt}\selectfont}",
        r"\everydisplay{\fontsize{7pt}{8.5pt}\selectfont}",
    )
    appendix_b = appendix_b.replace(
        r"\setlength{\tabcolsep}{3pt}",
        r"\setlength{\tabcolsep}{1.5pt}",
    )
    appendix_b = appendix_b.replace(
        r"\begin{tabular}{|p{0.18\linewidth}|p{0.72\linewidth}|}",
        r"\begin{tabular}{|p{0.15\linewidth}|p{0.79\linewidth}|}",
    )
    appendix_b = appendix_b.replace(r"\makebox[\linewidth][c]{$", r"$")
    appendix_b = appendix_b.replace(r"$} \\ \hline", r"$ \\ \hline")
    return prefix + appendix_b


class _ResultCacheController:
    def __init__(self, controller, cache: dict):
        self._controller = controller
        self._cache = cache

    def get_chunk(self, name: str):
        if name == "comparison_cache":
            return self._cache
        return _chunk(self._controller, name)


def _valid_result_cache(controller) -> dict:
    cache = _chunk(controller, "comparison_cache")
    if isinstance(cache, dict) and cache.get("is_valid") and cache.get("results"):
        return cache
    return {}


def _results_part(controller) -> str:
    cache = _valid_result_cache(controller)
    if not cache:
        return r"\textit{No calculated LCCA results available.}"
    latex = results_to_latex(_ResultCacheController(controller, cache))
    return wide_block(latex, size=r"\footnotesize")


def _plot_figure(plot_paths: dict | None, key: str, caption: str) -> str:
    filename = (plot_paths or {}).get(key)
    if not filename:
        return ""
    filename = str(filename).replace("\\", "/")
    return "\n".join([
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=0.88\textwidth]{" + filename + r"}",
        r"\caption{" + escape_latex(caption) + r"}",
        r"\end{figure}",
    ])


def _result_figures(plot_paths: dict | None) -> str:
    return "\n\n".join(part for part in [
        _plot_figure(plot_paths, KEY_PLOT_PILLAR_DONUT, "LCC components results"),
        _plot_figure(plot_paths, KEY_PLOT_STAGE_BARS, "Distribution of 3PS and 3 stages of LCC"),
        _plot_figure(plot_paths, KEY_PLOT_SUSTAINABILITY_MATRIX, "Distribution of 3PS and sustainability pillars of LCC"),
        _plot_figure(plot_paths, KEY_PLOT_PILLAR_BARS, "Distribution of various components of road user cost during construction"),
    ] if part and part.strip())


def _appendix_c_wpi(controller) -> str:
    latex = _call_exporter(controller, wpi_tables_to_latex, "WPI Tables")
    if not latex:
        return ""
    latex = latex.replace(r"\begin{landscape}", "").replace(r"\end{landscape}", "")
    latex = latex.replace(r"\begin{table}[h!]", r"\begin{table}[H]")
    return "\n\n".join([
        r"\clearpage",
        r"\begin{landscape}",
        r"\section*{Appendix C: Miscellaneous data}",
        r"\addcontentsline{toc}{section}{Appendix C: Miscellaneous data}",
        r"\begingroup",
        r"\scriptsize",
        r"\centering",
        r"\setlength{\tabcolsep}{2pt}",
        r"\setlength{\LTleft}{\fill}",
        r"\setlength{\LTright}{\fill}",
        latex,
        r"\normalsize",
        r"\endgroup",
        r"\end{landscape}",
    ])


def lcca_report_body(controller=None, plot_paths: dict | None = None) -> str:
    parts = [
        title_page(_project_name(controller)),
        front_matter(),
        introduction_to_latex(),
        clearpage(),
        section("Input data"),
        subsection("Bridge geometry and description"),
        _part(controller, "Bridge Data", bridge_data_to_latex),
        subsection("Financial inputs"),
        _part(controller, "Financial Data", financial_data_to_latex),
        subsection("Construction data"),
        _part(controller, "Structure Work Data", structure_work_data_to_latex, wide=True, size=r"\footnotesize"),
        subsection("Maintenance data"),
        _part(controller, "Maintenance Data", maintenance_data_to_latex),
        subsection("Traffic data"),
        _part(controller, "Traffic and Road Data", traffic_fields_to_latex),
        _part(controller, "Vehicle Traffic Data", vehicle_data_to_latex),
        _part(controller, "Traffic Diversion Emissions", diversion_emissions_to_latex),
        _part(controller, "Peak Hour Distribution", peak_hour_distribution_to_latex),
        subsection("Environmental input data"),
        _part(controller, "Social Cost Data", social_cost_data_to_latex),
        _part(controller, "Material Emissions", material_emissions_to_latex, wide=True, size=r"\scriptsize"),
        _part(controller, "Transport Emissions", transport_emissions_to_latex, wide=True, size=r"\tiny"),
        _part(controller, "Machinery and Equipment Emissions", machinery_emissions_to_latex, wide=True, size=r"\scriptsize"),
        subsection("Recycling data"),
        _part(controller, "Recycling", recycling_to_latex, wide=True, size=r"\scriptsize"),
        clearpage(),
        section("LCCA results"),
        subsection("Life cycle cost results"),
        _results_part(controller),
        _result_figures(plot_paths),
        clearpage(),
        _summary_from_v3_content(controller),
        clearpage(),
        _fit_appendix_b_tables(appendices_to_latex()),
        _appendix_c_wpi(controller),
    ]
    return "\n\n".join(part for part in parts if part and part.strip())


def build_structured_code_to_latex_report_document(controller=None, plot_paths: dict | None = None) -> str:
    return build_report_v3_document(
        lcca_report_body(controller, plot_paths)
    )


def _dedupe_lot_entries(lot_path: Path) -> None:
    if not lot_path.exists():
        return
    seen = set()
    output = []
    pattern = re.compile(r"\\contentsline \{table\}\{\\numberline \{([^}]*)\}")
    for line in lot_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = pattern.search(line)
        if not match:
            output.append(line)
            continue
        table_no = match.group(1)
        if table_no in seen:
            continue
        seen.add(table_no)
        output.append(line)
    lot_path.write_text("\n".join(output) + "\n", encoding="utf-8")


def _copy_static_assets(work_dir: Path) -> None:
    src = Path(__file__).resolve().parent / "images" / "image_1.png"
    if not src.exists():
        return

    dst = work_dir.parent / "pdf_generation_v3" / "images" / "image_1.png"
    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.resolve() == dst.resolve():
        return

    shutil.copy2(src, dst)


def compile_lcca_report_pdf(
    controller=None,
    output_dir: str | Path | None = None,
    filename: str = "structured_code_to_latex_report",
    keep_artifacts: bool = False,
) -> tuple[Path, Path]:
    try:
        from three_ps_lcca_gui.gui.components.utils.common_requested_data import set_controller
        set_controller(controller)
    except Exception:
        pass

    if output_dir is None:
        output_dir = Path(__file__).resolve().parent / "tests"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    final_tex_path = output_dir / f"{filename}.tex"
    final_pdf_path = output_dir / f"{filename}.pdf"

    cleanup = None
    try:
        if keep_artifacts:
            work_dir = output_dir
        else:
            cleanup = tempfile.TemporaryDirectory(prefix="3psLCCA_report_")
            work_dir = Path(cleanup.name)

        tex_path = work_dir / f"{filename}.tex"
        pdf_path = work_dir / f"{filename}.pdf"
        _copy_static_assets(work_dir)

        plot_paths = {}
        try:
            from three_ps_lcca_gui.report.plot_exporter import generate_plots
            cache = _valid_result_cache(controller)
            if cache.get("results"):
                currency = (
                    cache.get("currency")
                    or _chunk(controller, "general_info").get("project_currency")
                    or "INR"
                )
                plot_paths = generate_plots(cache["results"], str(work_dir), str(currency))
        except Exception as exc:
            print(f"[structured_code_to_latex_report] chart generation failed: {exc}")

        tex_path.write_text(
            build_structured_code_to_latex_report_document(controller, plot_paths),
            encoding="utf-8",
        )

        lot_path = tex_path.with_suffix(".lot")
        for _ in range(3):
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", tex_path.name],
                cwd=work_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            _dedupe_lot_entries(lot_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF was not generated: {pdf_path}")

        if pdf_path.resolve() != final_pdf_path.resolve():
            shutil.copy2(pdf_path, final_pdf_path)

        return final_tex_path, final_pdf_path

    finally:
        if cleanup is not None:
            cleanup.cleanup()
