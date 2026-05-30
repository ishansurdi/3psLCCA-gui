
import os

from .mod_base_report import LCCAReportBase
from .mod_lcca_template import LCCATemplate
from .constants import KEY_SHOW_TITLE_PAGE, KEY_SHOW_INTRODUCTION, KEY_SHOW_LCCA_RESULTS
from .sections.title_page import add_title_page
from .sections.introduction import add_introduction
from .mod_input_data import add_input_data
from .mod_traffic_data import add_traffic_data
from .mod_environmental_data import add_environmental_data
from .mod_results import add_lcca_results
from .sections.appendix import add_full_appendix
from .plot_exporter import generate_plots
from pylatex import NoEscape

class LCCAReportLatex(LCCAReportBase):

    def save_latex(self, filename="LCCA_Report", output_dir=None):
        if not output_dir:
            output_dir = os.getcwd()
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, filename)
        self.generate_tex(path)
        return path + ".tex"

    def generate_pdf_output(self, filename="LCCA_Report", output_dir=None):
        import subprocess
        if not output_dir:
            output_dir = os.getcwd()
        tex_path = os.path.join(output_dir, filename + ".tex")
        pdf_path = os.path.join(output_dir, filename + ".pdf")
        try:
            # Run pdflatex twice so \tableofcontents page numbers resolve correctly
            for _ in range(2):
                subprocess.run(
                    [self.LATEX_EXEC, "-interaction=nonstopmode", tex_path],
                    cwd=output_dir,
                    capture_output=True,
                )
            return pdf_path if os.path.exists(pdf_path) else None
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None


def generate_report(output_filename="LCCA_Report", export_dict=None, config_override=None, output_dir=None):
    """Entry point for report generation."""
    if not export_dict:
        raise ValueError("export_dict is required")

    template = LCCATemplate(export_dict)
    config = template.get_config()
    if config_override:
        config.update(config_override)
    data = template.get_report_data()

    # Generate chart PNGs into the same directory as the .tex file so that
    # pdflatex can resolve them by filename alone (no path prefix needed).
    _results  = export_dict.get("results", {})
    _currency = export_dict.get("inputs", {}).get("general_info", {}).get("project_currency", "INR")
    _out_dir  = output_dir or os.getcwd()
    try:
        data.update(generate_plots(_results, _out_dir, _currency))
    except Exception as _e:
        print(f"[lcca_generate] chart generation failed: {_e}")

    doc = LCCAReportLatex()

    # 1. Title page
    if config.get(KEY_SHOW_TITLE_PAGE, True):
        data["report_title"] = "LCCA Modular Report"
        add_title_page(doc, config, data)

     # 2. Table of contents
    doc.append(NoEscape(r"\newpage"))
    doc.append(NoEscape(r"\tableofcontents"))
    doc.append(NoEscape(r"\newpage"))

    # 2. Introduction (optional)
    if config.get(KEY_SHOW_INTRODUCTION, False):
        add_introduction(doc, config, data)

    # 3. Input data modules
    add_input_data(doc, config, data)
    add_traffic_data(doc, config, data)
    add_environmental_data(doc, config, data)

    # 4. LCCA Results
    if config.get(KEY_SHOW_LCCA_RESULTS, True):
        add_lcca_results(doc, config, data)

    # 5. Appendix
    add_full_appendix(doc)

    doc.save_latex(filename=output_filename, output_dir=output_dir)
    return doc.generate_pdf_output(filename=output_filename, output_dir=output_dir)

