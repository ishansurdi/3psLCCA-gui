import os
import sys
import json
import subprocess
from pathlib import Path

FILE_PATH     = Path(__file__).resolve()
DOC_BUILD_DIR = FILE_PATH.parent / "doc_build"

_LOCK_FILE = FILE_PATH.parent / ".glossary.lock"
_NAV_FILE  = FILE_PATH.parent / ".glossary.nav"

def _no_build_html() -> str:
    favicon = ""
    try:
        import base64
        from importlib.resources import files, as_file
        svg_ref = files("three_ps_lcca_gui.gui") / "assets" / "logo" / "logo-3psLCCA.svg"
        with as_file(svg_ref) as svg_path:
            b64 = base64.b64encode(svg_path.read_bytes()).decode()
            favicon = f'<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{b64}">'
    except Exception:
        pass
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Glossary</title>
{favicon}
<style>
body{{font-family:'Segoe UI',sans-serif;display:flex;align-items:center;
     justify-content:center;height:100vh;margin:0;background:#1e1e2e;color:#cdd6f4}}
.box{{text-align:center;max-width:440px}}
h2{{margin:0 0 12px;font-size:1.3em;color:#f38ba8}}
p{{margin:0 0 8px;font-size:14px;color:#a6adc8;line-height:1.6}}
strong{{color:#cdd6f4}}
</style>
</head>
<body>
<div class="box">
  <h2>Docs not built yet</h2>
  <p>Open <strong>Developer Tools &rarr; Doc Builder</strong> and click
     <strong>Build Docs</strong> to generate the glossary.</p>
  <p>Run once; the output is cached until you clean or rebuild.</p>
</div>
</body>
</html>"""


def _is_running() -> bool:
    if not _LOCK_FILE.exists():
        return False
    try:
        import psutil
        pid = int(_LOCK_FILE.read_text().strip())
        proc = psutil.Process(pid)
        if str(FILE_PATH) in proc.cmdline():
            return True
        # PID recycled by a different process - stale lock
        _LOCK_FILE.unlink(missing_ok=True)
        return False
    except (ValueError, OSError, psutil.NoSuchProcess, psutil.AccessDenied):
        _LOCK_FILE.unlink(missing_ok=True)
        return False


def _resolve(slug_parts: list | None) -> dict:
    if DOC_BUILD_DIR.exists():
        if slug_parts and len(slug_parts) >= 2:
            p = DOC_BUILD_DIR / slug_parts[0] / (slug_parts[1] + ".html")
            if p.exists():
                return {"url": p.as_uri()}
        for cat in sorted(DOC_BUILD_DIR.iterdir()):
            if cat.is_dir():
                for f in sorted(cat.glob("*.html")):
                    return {"url": f.as_uri()}
    return {"html": _no_build_html()}


def _get_theme() -> dict:
    try:
        from three_ps_lcca_gui.gui.themes import get_token
        return {
            "bg":         get_token("window"),
            "text":       get_token("text"),
            "sidebar_bg": get_token("surface"),
            "accent":     get_token("primary"),
            "border":     get_token("border"),
        }
    except Exception:
        return {}


class GlossaryAPI:
    def __init__(self, theme=None):
        self.theme = theme or {}
        _LOCK_FILE.write_text(str(os.getpid()))

    def _cleanup(self):
        _LOCK_FILE.unlink(missing_ok=True)
        _NAV_FILE.unlink(missing_ok=True)

    def get_theme(self):
        return self.theme

    def poll_navigation(self):
        if _NAV_FILE.exists():
            path = _NAV_FILE.read_text(encoding="utf-8").strip()
            _NAV_FILE.unlink(missing_ok=True)
            return path
        return None


def _icon_path() -> str | None:
    # parents[3]: doc_handler → utils → components → gui
    ico = Path(__file__).resolve().parents[3] / "assets" / "logo" / "logo-3psLCCA.ico"
    return str(ico) if ico.is_file() else None


def run():
    import webview
    slug  = json.loads(sys.argv[1]) if len(sys.argv) > 1 else None
    theme = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None

    api = GlossaryAPI(theme)
    webview.create_window("Glossary", js_api=api, width=1100, height=750, **_resolve(slug))
    webview.start(gui="edgechromium" if os.name == "nt" else None, icon=_icon_path())
    api._cleanup()


def open_glossary(slug_parts=None) -> None:
    if _is_running():
        if slug_parts:
            _NAV_FILE.write_text("/".join(slug_parts) + ".md", encoding="utf-8")
        return
    subprocess.Popen(
        [sys.executable, str(FILE_PATH),
         json.dumps(slug_parts or []), json.dumps(_get_theme())],
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


if __name__ == "__main__":
    run()
