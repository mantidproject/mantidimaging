# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-app-imports", action="store_true")
    args = parser.parse_args()

    if args.with_app_imports:
        from mantidimaging.gui.windows.main.view import MainWindowView  # noqa: F401

    from mantidimaging.gui.font_utils import configure_qt_font_directory
    from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
    from PyQt6.QtWidgets import QApplication
    import pyqtgraph as pg

    configure_qt_font_directory()
    app = QApplication([])
    plot = pg.PlotWidget()
    plot.resize(640, 480)
    plot.plot([0, 1, 2, 3], [0, 1, 4, 9])
    plot.show()
    for _ in range(10):
        app.processEvents()
        plot.repaint()
        app.processEvents()

    print(
        f"mode={'app-imports' if args.with_app_imports else 'minimal'}, "
        f"Qt={QT_VERSION_STR}, PyQt={PYQT_VERSION_STR}, PyQtGraph={pg.__version__}, "
        f"axis_picture_created={plot.getPlotItem().getAxis('bottom').picture is not None}",
        flush=True,
    )
    plot.close()
    app.processEvents()


if __name__ == "__main__":
    main()
