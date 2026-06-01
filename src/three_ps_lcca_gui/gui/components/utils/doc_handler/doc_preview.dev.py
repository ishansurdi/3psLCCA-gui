#!/usr/bin/env python
"""
doc_preview.dev.py  -  dev launcher for the GlossaryDialog.

Run from anywhere:
    python src/three_ps_lcca_gui/gui/components/utils/doc_handler/doc_preview.dev.py
    python ...doc_preview.dev.py  Financial_data Discount_rate
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[4]))   # .../src/

from PySide6.QtWidgets import QApplication

from three_ps_lcca_gui.gui.components.utils.doc_handler.glossary import open_glossary

if __name__ == "__main__":
    app = QApplication(sys.argv)

    try:
        from three_ps_lcca_gui.gui.themes import theme_manager
        theme_manager()
    except Exception:
        pass

    slug = sys.argv[1:] or None
    open_glossary(slug)
    sys.exit(app.exec())
