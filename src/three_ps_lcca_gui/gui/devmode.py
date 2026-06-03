import os
from PySide6.QtWidgets import QMenu, QMessageBox
from PySide6.QtGui import QAction
from three_ps_lcca_gui.gui.version import DEV_MODE

def setup_dev_menu(parent_window, menubar):
    """
    Sets up the 'Dev' menu in the provided menubar if DEV_MODE is active.
    
    Args:
        parent_window: The QMainWindow instance (usually ProjectWindow).
        menubar: The QMenuBar instance where the menu should be added.
    """
    if not DEV_MODE:
        return None

    dev_menu = QMenu("&Dev", menubar)
    
    # --- Pesticide Debugger Submenu ---
    pesticide_menu = QMenu("Pesticide Debugger", dev_menu)
    
    def set_pesticide(mode):
        try:
            from three_ps_lcca_gui.gui.themes.PESTICIDE import paraside
            paraside(mode)
        except ImportError:
            QMessageBox.warning(parent_window, "Pesticide", "Pesticide module not found.")

    action_p_rainbow = QAction("Mode: Rainbow", parent_window)
    action_p_rainbow.triggered.connect(lambda: set_pesticide("rainbow"))
    pesticide_menu.addAction(action_p_rainbow)

    action_p_beast = QAction("Mode: Beast", parent_window)
    action_p_beast.triggered.connect(lambda: set_pesticide("beast"))
    pesticide_menu.addAction(action_p_beast)

    pesticide_menu.addSeparator()

    action_p_off = QAction("Turn OFF", parent_window)
    action_p_off.triggered.connect(lambda: set_pesticide("off"))
    pesticide_menu.addAction(action_p_off)

    dev_menu.addMenu(pesticide_menu)
    
    # --- Live Inspector Toggle ---
    action_inspector = QAction("Toggle Inspector", parent_window)
    action_inspector.triggered.connect(lambda: set_pesticide("beast"))
    dev_menu.addAction(action_inspector)

    # --- LaTeX Submenu ---
    # Each entry: (menu label, module path, function name, output filename)
    _LATEX_ENTRIES = [
        ("Bridge Data",    "three_ps_lcca_gui.code_to_latex.bridge_data_latex",    "bridge_data_to_latex",    "bridge_data.tex"),
        ("Financial Data",    "three_ps_lcca_gui.code_to_latex.financial_data_latex",    "financial_data_to_latex",    "financial_data.tex"),
        ("Maintenance Data", "three_ps_lcca_gui.code_to_latex.maintenance_data_latex", "maintenance_data_to_latex", "maintenance_data.tex"),
        ("Vehicle Traffic Data", "three_ps_lcca_gui.code_to_latex.traffic_data_latex", "vehicle_traffic_data_to_latex", "vehicle_traffic_data.tex"),
    ]

    def _make_save_latex(module_path, fn_name, filename):
        def _handler():
            try:
                from pathlib import Path
                import importlib
                mod = importlib.import_module(module_path)
                fn = getattr(mod, fn_name)
                tests_dir = Path(__file__).parent.parent / "code_to_latex" / "tests"
                tests_dir.mkdir(exist_ok=True)
                out_path = tests_dir / filename
                doc = "\n".join([
                    r"\documentclass{article}",
                    r"\usepackage{booktabs}",
                    r"\usepackage[margin=1in]{geometry}",
                    r"\begin{document}",
                    fn(parent_window.controller),
                    r"\end{document}",
                ])
                out_path.write_text(doc, encoding="utf-8")
                QMessageBox.information(parent_window, "LaTeX", f"Saved to:\n{out_path}")
            except Exception as exc:
                QMessageBox.critical(parent_window, "LaTeX Error", str(exc))
        return _handler

    latex_menu = QMenu("LaTeX", dev_menu)
    for label, module_path, fn_name, filename in _LATEX_ENTRIES:
        action = QAction(f"Save {label} (tests/)", parent_window)
        action.triggered.connect(_make_save_latex(module_path, fn_name, filename))
        latex_menu.addAction(action)
    dev_menu.addMenu(latex_menu)

    # --- Add to Menubar ---
    menubar.addMenu(dev_menu)
    return dev_menu
