#!/usr/bin/env python
"""
doc_preview.dev.py  -  dev file-picker that drives the real doc_handler viewer.

Run from anywhere:
    python src/three_ps_lcca_gui/gui/components/utils/doc_handler/doc_preview.dev.py
    python ...doc_preview.dev.py  path/to/any/docs/folder

Clicking a file opens / updates the original QDialog viewer (same as in-app).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# ── path bootstrap: add src/ so package imports resolve without pip install ──
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[4]))   # .../src/

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QToolBar,
)

import three_ps_lcca_gui.gui.components.utils.doc_handler as _dh


class _PickerWindow(QMainWindow):
    def __init__(self, start_dir: Path) -> None:
        super().__init__()
        self.setWindowTitle("Doc Preview - file picker")
        self.resize(340, 640)

        # ── toolbar ──────────────────────────────────────────────────────────
        tb = QToolBar()
        tb.setMovable(False)
        tb.setFloatable(False)
        self.addToolBar(tb)

        btn = QPushButton("Open folder…")
        btn.clicked.connect(self._choose_folder)
        tb.addWidget(btn)

        self._folder_label = QLabel()
        self._folder_label.setContentsMargins(10, 0, 0, 0)
        tb.addWidget(self._folder_label)

        # ── file list ─────────────────────────────────────────────────────────
        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_select)
        self.setCentralWidget(self._list)

        self._load_dir(start_dir)

    def _load_dir(self, folder: Path) -> None:
        self._current_dir = folder
        self._folder_label.setText(folder.name)
        self._folder_label.setToolTip(str(folder))
        self._list.clear()
        for p in sorted(folder.rglob("*.md")):
            item = QListWidgetItem(str(p.relative_to(folder)))
            item.setData(Qt.UserRole, p)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _choose_folder(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Select docs folder", str(self._current_dir)
        )
        if chosen:
            self._load_dir(Path(chosen))

    def _on_select(self, current: QListWidgetItem | None, _prev) -> None:
        if current is None:
            return
        path: Path = current.data(Qt.UserRole)
        content = path.read_text(encoding="utf-8")
        h1 = re.search(r'^#\s+(.+)', content, re.MULTILINE)
        title = h1.group(1).strip() if h1 else path.stem.replace("_", " ").replace("-", " ").title()

        # drive the real singleton viewer - same path as open_doc()
        _dh._content = content
        _dh._show(title, parent=None)


def main() -> None:
    app = QApplication(sys.argv)

    try:
        from three_ps_lcca_gui.gui.themes import theme_manager
        theme_manager()
    except Exception:
        pass

    start = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _dh.DOCS_DIR
    win = _PickerWindow(start)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
