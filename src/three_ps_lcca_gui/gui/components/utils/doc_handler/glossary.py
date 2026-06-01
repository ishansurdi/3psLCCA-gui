"""
doc_handler/glossary.py

User-facing glossary browser: category tree on the left, rendered markdown on the right.

Usage:
    from ..utils.doc_handler.glossary import open_glossary
    open_glossary()                               # open to first article
    open_glossary(["Financial_data", "Discount_rate"])  # jump to a specific article
"""
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QLineEdit, QSplitter, QTextBrowser,
    QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator,
    QVBoxLayout, QWidget,
)

import three_ps_lcca_gui.gui.components.utils.doc_handler as _dh
from three_ps_lcca_gui.gui.themes import get_token, theme_manager
from three_ps_lcca_gui.gui.theme import FS_BASE, FS_MD, RADIUS_SM, SP2, SP3


_SKIP = {"404.md"}


class GlossaryDialog(QDialog):
    """Singleton glossary browser with a category tree and inline markdown preview."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Glossary")
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.resize(1040, 700)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        root_layout.addWidget(splitter)

        # ── Left: navigation panel ───────────────────────────────────────────
        nav = QWidget()
        nav.setObjectName("GlossaryNav")
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(SP3, SP3, SP2, SP3)
        nav_layout.setSpacing(SP2)

        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Search glossary…")
        self._filter.setClearButtonEnabled(True)
        self._filter.textChanged.connect(self._apply_filter)
        nav_layout.addWidget(self._filter)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(14)
        self._tree.setObjectName("GlossaryTree")
        self._tree.setFocusPolicy(Qt.StrongFocus)
        self._tree.currentItemChanged.connect(self._on_select)
        nav_layout.addWidget(self._tree)

        splitter.addWidget(nav)

        # ── Right: content browser ───────────────────────────────────────────
        self._browser = QTextBrowser()
        self._browser.setObjectName("GlossaryBrowser")
        self._browser.setOpenExternalLinks(True)
        self._browser.setFrameShape(QTextBrowser.Shape.NoFrame)
        self._browser.document().setDocumentMargin(20)
        self._browser._zoom = 0
        self._browser.wheelEvent = self._wheel
        splitter.addWidget(self._browser)

        splitter.setSizes([260, 780])

        self._file_map: dict[QTreeWidgetItem, Path] = {}
        self._title_map: dict[QTreeWidgetItem, str] = {}
        self._current_content: str = ""

        self._build_tree()
        self._apply_nav_style()
        theme_manager().theme_changed.connect(self._on_theme_change)

    # ── tree ─────────────────────────────────────────────────────────────────

    def _build_tree(self) -> None:
        self._tree.clear()
        self._file_map.clear()
        self._title_map.clear()
        self._populate(self._tree.invisibleRootItem(), _dh.DOCS_DIR)
        self._tree.expandAll()
        self._select_first()

    def _populate(self, parent: QTreeWidgetItem, folder: Path) -> None:
        for entry in sorted(folder.iterdir()):
            if entry.is_dir() and any(entry.rglob("*.md")):
                label = entry.name.replace("_", " ").title()
                group = QTreeWidgetItem(parent, [label])
                group.setFlags(group.flags() & ~Qt.ItemIsSelectable)
                f = QFont()
                f.setPointSize(FS_MD)
                f.setWeight(QFont.Weight.DemiBold)
                group.setFont(0, f)
                self._populate(group, entry)
            elif entry.suffix == ".md" and entry.name not in _SKIP:
                content = entry.read_text(encoding="utf-8")
                h1 = re.search(r'^#\s+(.+)', content, re.MULTILINE)
                label = (
                    h1.group(1).strip() if h1
                    else entry.stem.replace("_", " ").replace("-", " ").title()
                )
                item = QTreeWidgetItem(parent, [label])
                item.setData(0, Qt.UserRole, (entry, content))
                self._file_map[item] = entry
                self._title_map[item] = label

    def _select_first(self) -> None:
        it = QTreeWidgetItemIterator(
            self._tree, QTreeWidgetItemIterator.IteratorFlag.Selectable
        )
        first = it.value()
        if first:
            self._tree.setCurrentItem(first)

    # ── selection / rendering ────────────────────────────────────────────────

    def _on_select(self, current: QTreeWidgetItem | None, _prev) -> None:
        if current is None:
            return
        data = current.data(0, Qt.UserRole)
        if data is None:
            return
        _path, content = data
        self._current_content = content
        title = self._title_map.get(current, "Glossary")
        self.setWindowTitle(f"Glossary — {title}")
        self._rerender()

    def _rerender(self) -> None:
        if not self._current_content:
            return
        sb = self._browser.verticalScrollBar()
        pos = sb.value()
        _dh._render(self._browser, self._current_content)
        sb.setValue(pos)

    # ── search filter ────────────────────────────────────────────────────────

    def _apply_filter(self, text: str) -> None:
        text = text.strip().lower()
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._filter_item(root.child(i), text)

    def _filter_item(self, item: QTreeWidgetItem, text: str) -> bool:
        label_match = not text or text in item.text(0).lower()
        child_visible = False
        for i in range(item.childCount()):
            child_visible |= self._filter_item(item.child(i), text)
        visible = label_match or child_visible
        item.setHidden(not visible)
        if text and child_visible:
            item.setExpanded(True)
        elif not text:
            item.setExpanded(True)
        return visible

    # ── zoom ─────────────────────────────────────────────────────────────────

    def _wheel(self, ev) -> None:
        if ev.modifiers() & Qt.ControlModifier:
            if ev.angleDelta().y() > 0:
                self._browser.zoomIn(2)
                self._browser._zoom += 2
            else:
                self._browser.zoomOut(2)
                self._browser._zoom -= 2
            self._rerender()
        else:
            QTextBrowser.wheelEvent(self._browser, ev)

    # ── theme ────────────────────────────────────────────────────────────────

    def _apply_nav_style(self) -> None:
        border  = get_token("border")
        surface = get_token("surface")
        text    = get_token("text")
        t_sec   = get_token("text_secondary")
        t_dis   = get_token("text_disabled")
        sel_bg  = get_token("surface", "pressed")
        hov_bg  = get_token("surface", "hover")
        win     = get_token("window")

        self._filter.setStyleSheet(f"""
            QLineEdit {{
                background: {surface};
                color: {text};
                border: 1px solid {border};
                border-radius: {RADIUS_SM}px;
                padding: {SP2}px {SP3}px;
                font-size: {FS_BASE}pt;
            }}
            QLineEdit:focus {{ border-color: {get_token("primary")}; }}
        """)

        primary = get_token("primary")

        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                border: none;
                outline: none;
                font-size: {FS_BASE}pt;
                selection-background-color: transparent;
                selection-color: {text};
            }}
            QTreeWidget::item {{
                padding: 5px {SP2}px;
                padding-left: {SP2 + 3}px;
                color: {t_sec};
                border-left: 3px solid transparent;
            }}
            QTreeWidget::item:hover:!selected {{
                background: {hov_bg};
                color: {text};
                border-left: 3px solid transparent;
            }}
            QTreeWidget::item:selected {{
                background: {sel_bg};
                color: {primary};
                border-left: 3px solid {primary};
                font-weight: 500;
            }}
            QTreeWidget::item:disabled {{
                color: {t_dis};
                border-left: 3px solid transparent;
            }}
            QTreeWidget::branch:selected {{
                background: {sel_bg};
            }}
            QTreeWidget::branch:hover:!selected {{
                background: {hov_bg};
            }}
        """)

        self.findChild(QWidget, "GlossaryNav").setStyleSheet(f"""
            #GlossaryNav {{
                background: {win};
                border-right: 1px solid {border};
            }}
        """)

    def _on_theme_change(self) -> None:
        self._apply_nav_style()
        self._rerender()

    # ── public API ───────────────────────────────────────────────────────────

    def navigate(self, slug_parts: list[str]) -> None:
        """Jump the tree selection to the article matching slug_parts."""
        target = _dh.DOCS_DIR.joinpath(*slug_parts).with_suffix(".md")
        for item, path in self._file_map.items():
            if path == target:
                self._tree.setCurrentItem(item)
                self._tree.scrollToItem(item)
                return


# ── module-level singleton + public entry point ──────────────────────────────

_glossary: GlossaryDialog | None = None


def open_glossary(
    slug_parts: list[str] | None = None,
    parent=None,
) -> None:
    """Open the glossary browser, optionally jumping to a specific article.

    Args:
        slug_parts: Path segments relative to DOCS_DIR, e.g.
                    ["Financial_data", "Discount_rate"].
                    Omit to open on the first article.
        parent:     Qt parent widget (used only on first creation).
    """
    global _glossary
    if _glossary is None:
        _glossary = GlossaryDialog(parent)
    if slug_parts:
        _glossary.navigate(slug_parts)
    _glossary.show()
    _glossary.raise_()
    _glossary.activateWindow()
