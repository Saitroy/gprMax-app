from __future__ import annotations

import os
import sys
from pathlib import Path

DEFAULT_QT_PLATFORM = "windows" if sys.platform.startswith("win") else "offscreen"
os.environ.setdefault("QT_QPA_PLATFORM", DEFAULT_QT_PLATFORM)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


VIEWPORTS = (
    (1366, 768),
    (1440, 900),
    (1920, 1080),
    (2560, 1440),
)

PAGES = (
    ("home", "page.welcome.title"),
    ("model", "page.project.title"),
    ("simulation", "page.simulation.title"),
    ("results", "page.results.title"),
)


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from gprmax_workbench.app import build_context
    from gprmax_workbench.ui.main_window import MainWindow
    from gprmax_workbench.ui.theme import apply_theme

    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app)
    context = build_context()
    window = MainWindow(context)
    target = ROOT / "artifacts" / "ui-redesign" / "final"
    target.mkdir(parents=True, exist_ok=True)

    for width, height in VIEWPORTS:
        window.resize(width, height)
        window.show()
        app.processEvents()
        for page_name, title_key in PAGES:
            page_index = window._page_index_by_title_key[title_key]  # noqa: SLF001
            window._show_page(page_index)  # noqa: SLF001
            app.processEvents()
            output = target / f"{width}x{height}-{page_name}.png"
            window.grab().save(str(output))

    window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
