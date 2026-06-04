"""
devtools/doc_builder_gui.py

Pre-builds the glossary docs/ folder into static HTML.
All conversion (Markdown + math) is handled by doc_build.js via Node.js.
No Python markdown package required.

Config: devtools/doc_builder_config.json
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout,
)

# ── Catppuccin Mocha palette ───────────────────────────────────────────────────
_BG     = "#1e1e2e"
_BG2    = "#252535"
_BG3    = "#313244"
_TEXT   = "#cdd6f4"
_DIM    = "#585b70"
_GREEN  = "#a6e3a1"
_RED    = "#f38ba8"
_YELLOW = "#f9e2af"
_BORDER = "#2a2a3e"

# ── paths ──────────────────────────────────────────────────────────────────────
_DEVTOOLS    = Path(__file__).parent
_PROJ_ROOT   = _DEVTOOLS.parent
_DOC_HANDLER = (_PROJ_ROOT / "src" / "three_ps_lcca_gui" / "gui"
                / "components" / "utils" / "doc_handler")
DOCS_DIR      = _DOC_HANDLER / "docs"
BUILD_DIR     = _DOC_HANDLER / "doc_build"
_CONFIG_FILE  = _DEVTOOLS / "doc_builder_config.json"
_NODE_MODULES = _DEVTOOLS / "node_modules"
_BUILD_SCRIPT = _DEVTOOLS / "doc_build.js"

# ── config ─────────────────────────────────────────────────────────────────────

_DEFAULTS = {"node_path": "node", "renderer": "katex"}


def _load_config() -> dict:
    if _CONFIG_FILE.exists():
        try:
            return {**_DEFAULTS, **json.loads(_CONFIG_FILE.read_text())}
        except Exception:
            pass
    return dict(_DEFAULTS)


def _save_config(cfg: dict) -> None:
    _CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


# ── node / npm helpers ─────────────────────────────────────────────────────────

def _detect_node() -> str:
    return shutil.which("node") or shutil.which("node.exe") or ""


def _npm() -> str:
    return shutil.which("npm") or shutil.which("npm.cmd") or "npm"


def _pkg_for(renderer: str) -> str:
    return "katex" if renderer == "katex" else "mathjax-full"


def _is_installed(renderer: str) -> bool:
    # Both katex/mathjax-full and marked are required
    return (
        (_NODE_MODULES / _pkg_for(renderer) / "package.json").exists()
        and (_NODE_MODULES / "marked" / "package.json").exists()
    )


def _npm_install(renderer: str) -> tuple[bool, str]:
    pkgs = [_pkg_for(renderer), "marked"]
    try:
        r = subprocess.run(
            [_npm(), "install"] + pkgs,
            capture_output=True, text=True, cwd=str(_DEVTOOLS), timeout=180,
        )
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as exc:
        return False, str(exc)


# ── build worker ───────────────────────────────────────────────────────────────

class _BuildWorker(QThread):
    log    = Signal(str)
    done   = Signal(int, float)
    failed = Signal(str)

    def __init__(self, node_path: str, renderer: str):
        super().__init__()
        self.node_path = node_path
        self.renderer  = renderer

    def run(self) -> None:
        try:
            t0 = time.perf_counter()
            self.done.emit(self._build(), time.perf_counter() - t0)
        except Exception:
            import traceback
            self.failed.emit(traceback.format_exc())

    def _build(self) -> int:
        proc = subprocess.Popen(
            [self.node_path, str(_BUILD_SCRIPT),
             self.renderer, str(DOCS_DIR), str(BUILD_DIR)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=str(_DEVTOOLS),
        )

        n = 0
        for raw in proc.stdout:
            line = raw.rstrip()
            if line.startswith("FILE "):
                self.log.emit(f"  {line[5:]}")
            elif line.startswith("ASSETS "):
                self.log.emit(f"  Copied {line[7:]} CSS + fonts")
            elif line.startswith("DONE "):
                n = int(line.split()[1])
            elif line.startswith("ERROR "):
                raise RuntimeError(line[6:])

        proc.wait()
        if proc.returncode != 0:
            err = proc.stderr.read().strip()
            raise RuntimeError(f"node exited {proc.returncode}:\n{err}")

        return n


# ── install worker ─────────────────────────────────────────────────────────────

class _InstallWorker(QThread):
    done = Signal(bool, str)

    def __init__(self, renderer: str):
        super().__init__()
        self.renderer = renderer

    def run(self) -> None:
        self.done.emit(*_npm_install(self.renderer))


# ── dialog ─────────────────────────────────────────────────────────────────────

class DocBuilderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Doc Builder")
        self.resize(700, 520)
        self.setStyleSheet(f"background:{_BG}; color:{_TEXT};")
        self._cfg      = _load_config()
        self._worker:   _BuildWorker   | None = None
        self._installer: _InstallWorker | None = None
        self._build_ui()
        self._refresh_pkg_status()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        root.addWidget(self._make_config_group())

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(
            f"background:{_BG2}; color:{_TEXT};"
            f" border:1px solid {_BORDER}; border-radius:4px;"
            f" font-family:Consolas,monospace; font-size:11px;"
        )
        root.addWidget(self._log, stretch=1)

        self._status_lbl = QLabel("Ready.")
        self._status_lbl.setStyleSheet(f"color:{_DIM}; font-size:11px;")
        root.addWidget(self._status_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._clean_btn = QPushButton("Clean Build")
        self._clean_btn.setFixedHeight(30)
        self._clean_btn.setStyleSheet(_btn_css(_BG3, _TEXT))
        self._clean_btn.clicked.connect(self._clean)
        btn_row.addWidget(self._clean_btn)
        btn_row.addStretch()

        self._build_btn = QPushButton("Build Docs")
        self._build_btn.setFixedHeight(30)
        self._build_btn.setFixedWidth(100)
        self._build_btn.setStyleSheet(_btn_css(_GREEN, "#1e1e2e"))
        self._build_btn.clicked.connect(self._start_build)
        btn_row.addWidget(self._build_btn)

        root.addLayout(btn_row)

    def _make_config_group(self) -> QGroupBox:
        grp = QGroupBox("Configuration")
        grp.setStyleSheet(
            f"QGroupBox {{ color:{_TEXT}; border:1px solid {_BORDER}; border-radius:4px;"
            f" margin-top:8px; font-size:11px; }}"
            f"QGroupBox::title {{ subcontrol-origin:margin; left:8px; padding:0 4px; }}"
        )
        gl = QVBoxLayout(grp)
        gl.setContentsMargins(12, 18, 12, 12)
        gl.setSpacing(8)

        # Node.js path
        nr = QHBoxLayout(); nr.setSpacing(6)
        nr.addWidget(_lbl("Node.js", 68))
        self._node_edit = QLineEdit(self._cfg.get("node_path", "node"))
        self._node_edit.setPlaceholderText("node  or  full path to node.exe")
        self._node_edit.setStyleSheet(_input_css())
        self._node_edit.textChanged.connect(self._on_node_changed)
        nr.addWidget(self._node_edit, stretch=1)
        det_btn = QPushButton("Auto-detect")
        det_btn.setFixedHeight(26)
        det_btn.setStyleSheet(_btn_css(_BG3, _TEXT, small=True))
        det_btn.clicked.connect(self._auto_detect)
        nr.addWidget(det_btn)
        gl.addLayout(nr)

        # Renderer
        rr = QHBoxLayout(); rr.setSpacing(6)
        rr.addWidget(_lbl("Renderer", 68))
        self._renderer_combo = QComboBox()
        self._renderer_combo.addItems(["katex", "mathjax"])
        self._renderer_combo.setCurrentText(self._cfg.get("renderer", "katex"))
        self._renderer_combo.setFixedWidth(100)
        self._renderer_combo.setStyleSheet(
            f"QComboBox {{ background:{_BG2}; color:{_TEXT}; border:1px solid {_BORDER};"
            f" border-radius:3px; padding:3px 8px; font-size:11px; }}"
            f"QComboBox QAbstractItemView {{ background:{_BG2}; color:{_TEXT}; }}"
        )
        self._renderer_combo.currentTextChanged.connect(self._on_renderer_changed)
        rr.addWidget(self._renderer_combo)
        self._pkg_lbl = QLabel()
        self._pkg_lbl.setStyleSheet(f"color:{_DIM}; font-size:11px;")
        rr.addWidget(self._pkg_lbl, stretch=1)
        self._install_btn = QPushButton("Install")
        self._install_btn.setFixedHeight(26)
        self._install_btn.setFixedWidth(80)
        self._install_btn.setStyleSheet(_btn_css(_YELLOW, "#1e1e2e", small=True))
        self._install_btn.clicked.connect(self._run_install)
        rr.addWidget(self._install_btn)
        gl.addLayout(rr)

        return grp

    # ── config callbacks ──────────────────────────────────────────────────────

    def _on_node_changed(self, text: str) -> None:
        self._cfg["node_path"] = text.strip()
        _save_config(self._cfg)

    def _on_renderer_changed(self, text: str) -> None:
        self._cfg["renderer"] = text
        _save_config(self._cfg)
        self._refresh_pkg_status()

    def _auto_detect(self) -> None:
        path = _detect_node()
        if path:
            self._node_edit.setText(path)
            self._log.appendPlainText(f"Found: {path}")
        else:
            self._log.appendPlainText("Node.js not found on PATH - install from https://nodejs.org")

    def _refresh_pkg_status(self) -> None:
        renderer = self._cfg.get("renderer", "katex")
        pkg = _pkg_for(renderer)
        if _is_installed(renderer):
            self._pkg_lbl.setText(f"{pkg} + marked ✓")
            self._pkg_lbl.setStyleSheet(f"color:{_GREEN}; font-size:11px;")
            self._install_btn.setText("Reinstall")
        else:
            self._pkg_lbl.setText(f"{pkg} + marked - not installed")
            self._pkg_lbl.setStyleSheet(f"color:{_RED}; font-size:11px;")
            self._install_btn.setText("Install")

    # ── install ───────────────────────────────────────────────────────────────

    def _run_install(self) -> None:
        renderer = self._cfg.get("renderer", "katex")
        self._log.appendPlainText(f"npm install {_pkg_for(renderer)} marked …")
        self._set_busy(True)
        self._installer = _InstallWorker(renderer)
        self._installer.done.connect(self._on_install_done)
        self._installer.start()

    def _on_install_done(self, ok: bool, out: str) -> None:
        if out:
            self._log.appendPlainText(out)
        self._refresh_pkg_status()
        self._set_busy(False)
        self._log.appendPlainText("Installation complete." if ok else "Installation failed.")

    # ── build ─────────────────────────────────────────────────────────────────

    def _start_build(self) -> None:
        renderer = self._cfg.get("renderer", "katex")
        if not _is_installed(renderer):
            self._log.appendPlainText(
                f"ERROR: {_pkg_for(renderer)} or marked is not installed. Click Install first."
            )
            return

        self._log.clear()
        self._log.appendPlainText(f"Building with {renderer}…\n")
        self._set_busy(True)
        self._set_status("Building…", _DIM)

        self._worker = _BuildWorker(
            node_path=self._cfg.get("node_path", "node"),
            renderer=renderer,
        )
        self._worker.log.connect(self._log.appendPlainText)
        self._worker.done.connect(self._on_build_done)
        self._worker.failed.connect(self._on_build_failed)
        self._worker.start()

    def _on_build_done(self, n: int, elapsed: float) -> None:
        self._set_status(f"Done - {n} file(s) in {elapsed:.1f} s", _GREEN)
        self._log.appendPlainText(f"\nOutput → {BUILD_DIR}")
        self._set_busy(False)

    def _on_build_failed(self, msg: str) -> None:
        self._log.appendPlainText(f"\n{msg}")
        self._set_status("Build failed - see log above.", _RED)
        self._set_busy(False)

    def _clean(self) -> None:
        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)
            self._log.appendPlainText(f"Removed {BUILD_DIR}")
            self._set_status("Cleaned.", _DIM)
        else:
            self._log.appendPlainText("Nothing to clean.")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _set_busy(self, busy: bool) -> None:
        self._build_btn.setEnabled(not busy)
        self._clean_btn.setEnabled(not busy)
        self._install_btn.setEnabled(not busy)

    def _set_status(self, text: str, color: str) -> None:
        self._status_lbl.setText(text)
        self._status_lbl.setStyleSheet(f"color:{color}; font-size:11px;")


# ── style helpers ──────────────────────────────────────────────────────────────

def _btn_css(bg: str, fg: str, small: bool = False) -> str:
    fs = "10px" if small else "11px"
    return (
        f"QPushButton {{ background:{bg}; color:{fg}; border:none;"
        f" border-radius:4px; font-weight:bold; font-size:{fs}; }}"
        f"QPushButton:hover:enabled {{ background:#3a3a5a; color:{_TEXT}; }}"
        f"QPushButton:disabled {{ background:{_BG3}; color:{_DIM}; }}"
    )


def _input_css() -> str:
    return (
        f"QLineEdit {{ background:{_BG2}; color:{_TEXT}; border:1px solid {_BORDER};"
        f" border-radius:3px; padding:3px 8px; font-size:11px; }}"
        f"QLineEdit:focus {{ border-color:#89b4fa; }}"
    )


def _lbl(text: str, width: int) -> QLabel:
    lb = QLabel(text)
    lb.setFixedWidth(width)
    lb.setStyleSheet(f"color:{_DIM}; font-size:11px;")
    return lb
