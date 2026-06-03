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

    # --- Add to Menubar ---
    menubar.addMenu(dev_menu)
    return dev_menu
