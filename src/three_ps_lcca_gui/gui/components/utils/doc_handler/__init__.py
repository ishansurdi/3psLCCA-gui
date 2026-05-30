r"""
gui/components/utils/doc_handler/__init__.py

Singleton in-app Markdown doc viewer built on QTextBrowser.
Zoom: Ctrl + scroll wheel.

LaTeX math support
------------------
Use $...$ for inline and $$...$$ for display math in .md files.
Expressions are rendered via matplotlib.mathtext (no system LaTeX required).
If matplotlib is not installed the raw delimiters are shown as-is.

Usage:
    from ..utils.doc_handler import open_doc
    open_doc(["Bridge_data", "Wind_Speed"])
"""

from __future__ import annotations

import base64
import io
import re
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFontMetrics, QPalette, QPixmap, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument, QTextImageFormat
from PySide6.QtWidgets import QApplication, QDialog, QTextBrowser, QVBoxLayout

from three_ps_lcca_gui.gui.themes import get_token, theme_manager
from three_ps_lcca_gui.gui.theme import FS_LG, FS_SUBHEAD, FS_BASE


DOCS_DIR = Path(__file__).parent / "docs"

_dialog:  QDialog      | None = None
_browser: QTextBrowser | None = None
_content: str                 = ""

_REF_RE = re.compile(
    r'^\[([^\]]+)\]:\s*<?(data:image/[^>\s][^>]*?)>?\s*$',
    re.MULTILINE,
)
_IMG_RE = re.compile(r'!\[([^\]]*)\]\[([^\]]+)\]')

# $$...$$ for display math, $...$ for inline - display matched first to avoid
# treating $$ as two inline delimiters; [^$] in inline prevents crossing $$
_DISPLAY_MATH_RE = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
_INLINE_MATH_RE  = re.compile(r'\$([^$\n]+?)\$')

# Cache keyed by (expr, display, text_color).  One extra entry per theme but
# avoids fragile post-hoc SVG colour replacement.
_latex_cache: dict[tuple, str] = {}


def _render_latex_svg(expr: str, display: bool = False,
                      text_color: str = "black") -> str | None:
    """Render a LaTeX expression to an SVG string via matplotlib.mathtext.

    Uses Figure + FigureCanvasSVG directly (no pyplot) to avoid backend
    conflicts when Qt has already claimed the display.
    Returns None if matplotlib is unavailable or the expression is invalid.
    """
    try:
        import matplotlib as mpl
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_svg import FigureCanvasSVG
    except ImportError:
        return None

    try:
        fontsize = FS_BASE
        _ubuntu_ctx = {
            'mathtext.fontset': 'custom',
            'mathtext.rm': 'Ubuntu',
            'mathtext.it': 'Ubuntu',
            'mathtext.bf': 'Ubuntu',
            'mathtext.sf': 'Ubuntu',
            'mathtext.cal': 'Ubuntu',
            'mathtext.tt': 'Ubuntu',
        }
        with mpl.rc_context(_ubuntu_ctx):
            fig = Figure(figsize=(0.01, 0.01), facecolor="none")
            FigureCanvasSVG(fig)
            # No axes - fig.text tight-bbox clips to the glyph extent only.
            # ha="left" at x=0 ensures no centering whitespace on the right.
            fig.text(
                0, 0.5,
                f"${expr.strip()}$",
                fontsize=fontsize,
                color=text_color,
                ha="left", va="center",
            )
            buf = io.BytesIO()
            fig.savefig(buf, format="svg", bbox_inches="tight",
                        pad_inches=0.02, transparent=True)
        return buf.getvalue().decode("utf-8")
    except Exception:
        return None


def _svg_to_b64png(svg: str) -> str | None:
    """Rasterise an SVG string to a base64 PNG via QSvgRenderer."""
    try:
        from PySide6.QtSvg import QSvgRenderer
        from PySide6.QtCore import QBuffer, QByteArray, QIODevice
        from PySide6.QtGui import QPainter
    except ImportError:
        return None

    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    if not renderer.isValid():
        return None

    size = renderer.defaultSize()
    # 3× oversample keeps paths crisp after Qt scales the image down
    pixmap = QPixmap(size.width() * 3, size.height() * 3)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()

    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buf, "PNG")
    buf.close()
    return base64.b64encode(bytes(buf.data())).decode("utf-8")


def _preprocess_latex(content: str, text_color: str = "") -> str:
    """Replace \\[...\\] and \\(...\\) blocks with embedded PNG image references."""
    if not text_color:
        text_color = get_token("text") or "#000000"

    counter = [0]
    ref_lines: list[str] = []

    def _sub(expr: str, display: bool) -> str:
        key = (expr.strip(), display, text_color)
        if key not in _latex_cache:
            svg = _render_latex_svg(expr, display, text_color=text_color)
            if svg is None:
                delim = "$$" if display else "$"
                return f"{delim}{expr}{delim}"
            _latex_cache[key] = svg
        b64 = _svg_to_b64png(_latex_cache[key])
        if b64 is None:
            delim = "$$" if display else "$"
            return f"{delim}{expr}{delim}"
        idx = counter[0]
        counter[0] += 1
        # ltxd = display block, ltxi = inline - consumed by _render for sizing
        tok = f"ltxd{idx}" if display else f"ltxi{idx}"
        ref_lines.append(f"[{tok}]: <data:image/png;base64,{b64}>")
        return f"![eq][{tok}]"

    def sub_display(m: re.Match) -> str:
        return f"\n\n{_sub(m.group(1), display=True)}\n\n"

    def sub_inline(m: re.Match) -> str:
        return _sub(m.group(1), display=False)

    content = _DISPLAY_MATH_RE.sub(sub_display, content)
    content = _INLINE_MATH_RE.sub(sub_inline, content)

    if ref_lines:
        content += "\n\n" + "\n".join(ref_lines)

    return content


def _render(browser: QTextBrowser, content: str) -> None:
    text_color = browser.palette().color(QPalette.ColorRole.Text).name()
    content = _preprocess_latex(content, text_color=text_color)

    refs = {m.group(1): m.group(2) for m in _REF_RE.finditer(content)}

    if not refs:
        browser.setMarkdown(content)
        return

    tokens: dict[str, str] = {}
    n = [0]

    def _tok(m: re.Match) -> str:
        key = m.group(2)
        if key not in refs:
            return m.group(0)
        # preserve inline/display tag: ltxi→DOCIMGi, ltxd→DOCIMGd, other→DOCIMG
        prefix = "DOCIMGi" if key.startswith("ltxi") else ("DOCIMGd" if key.startswith("ltxd") else "DOCIMG")
        tok = f"{prefix}{n[0]}"
        tokens[tok] = refs[key]
        n[0] += 1
        return tok

    text = _IMG_RE.sub(_tok, _REF_RE.sub("", content))
    browser.setMarkdown(text)

    default_pt = QApplication.font().pointSizeF()
    current_pt = browser.font().pointSizeF()
    zoom   = current_pt / default_pt if default_pt > 0 else 1.0
    screen = QApplication.primaryScreen()
    dpr    = screen.devicePixelRatio() if screen else 1.0

    doc = browser.document()
    line_h = QFontMetrics(browser.font()).height()
    for i, (tok, uri) in enumerate(tokens.items()):
        is_inline = tok.startswith("DOCIMGi")
        img_name = f"docimg{i}.png"
        try:
            _, _, enc = uri.partition(",")
            src = QPixmap()
            src.loadFromData(base64.b64decode(enc))
            if src.isNull():
                continue
            if is_inline:
                aspect    = src.width() / src.height() if src.height() > 0 else 1.0
                logical_h = max(1, int(line_h * zoom * 1.0))
                logical_w = max(1, int(logical_h * aspect))
                physical_h = max(1, int(logical_h * dpr))
                scaled = src.scaledToHeight(physical_h, Qt.SmoothTransformation)
            else:
                physical_w = max(1, int(src.width() * zoom))
                logical_w  = max(1, int(physical_w / dpr))
                logical_h  = 0
                scaled = (
                    src.scaledToWidth(physical_w, Qt.SmoothTransformation)
                    if src.width() != physical_w else src
                )
            doc.addResource(
                QTextDocument.ResourceType.ImageResource,
                QUrl(img_name),
                scaled,
            )
        except Exception:
            continue

        fmt = QTextImageFormat()
        fmt.setName(img_name)
        fmt.setWidth(logical_w)
        if is_inline:
            fmt.setHeight(logical_h)
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignMiddle)

        cur = doc.find(tok)
        while not cur.isNull():
            cur.insertImage(fmt)
            if not is_inline:
                block_fmt = cur.blockFormat()
                block_fmt.setAlignment(Qt.AlignHCenter)
                cur.setBlockFormat(block_fmt)
            cur = doc.find(tok)


def open_doc(slug_parts: list[str], parent=None) -> None:
    global _content

    if not slug_parts:
        return

    md_path = DOCS_DIR.joinpath(*slug_parts).with_suffix(".md")
    if not md_path.exists():
        fallback = DOCS_DIR / "404.md"
        if not fallback.exists():
            return
        md_path = fallback

    _content = md_path.read_text(encoding="utf-8")
    h1 = re.search(r'^#\s+(.+)', _content, re.MULTILINE)
    title = h1.group(1).strip() if h1 else md_path.stem.replace("_", " ").replace("-", " ").title()
    _show(title, parent)


def close_doc() -> None:
    global _dialog
    if _dialog is not None:
        _dialog.close()


def _show(title: str, parent=None) -> None:
    global _dialog, _browser

    if QApplication.instance() is None:
        return

    if _dialog is None:
        _dialog = QDialog(parent)
        _dialog.setWindowFlags(Qt.Window)
        _dialog.resize(860, 640)
        _dialog.setAttribute(Qt.WA_DeleteOnClose, False)

        layout = QVBoxLayout(_dialog)
        layout.setContentsMargins(0, 0, 0, 0)

        _browser = QTextBrowser()
        _browser.setObjectName("_doc_browser")
        _browser.setOpenExternalLinks(True)
        _browser.setFrameShape(QTextBrowser.Shape.NoFrame)
        layout.addWidget(_browser)

        _browser._zoom = 0

        def _rerender():
            sb  = _browser.verticalScrollBar()
            pos = sb.value()
            _render(_browser, _content)
            sb.setValue(pos)

        def _zoom_in():
            _browser.zoomIn(2); _browser._zoom += 2; _rerender()

        def _zoom_out():
            _browser.zoomOut(2); _browser._zoom -= 2; _rerender()

        def _wheel(ev):
            if ev.modifiers() & Qt.ControlModifier:
                _zoom_in() if ev.angleDelta().y() > 0 else _zoom_out()
            else:
                QTextBrowser.wheelEvent(_browser, ev)

        _browser.wheelEvent = _wheel

        theme_manager().theme_changed.connect(_rerender)

    elif parent is not None:
        _dialog.setParent(parent)
        _dialog.setWindowFlags(Qt.Window)

    # reset zoom on new doc
    z = getattr(_browser, "_zoom", 0)
    if z > 0:  _browser.zoomOut(z)
    elif z < 0: _browser.zoomIn(-z)
    _browser._zoom = 0

    _render(_browser, _content)

    _dialog.setWindowTitle(title)
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()
