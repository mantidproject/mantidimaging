from __future__ import annotations

from importlib.resources import files

from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication

_font_family: str | None = None


def load_application_font(app: QApplication) -> str | None:
    global _font_family

    if _font_family is None:
        font_path = files("qt_material").joinpath("fonts", "roboto", "Roboto-Regular.ttf")
        if not font_path.is_file():
            return None

        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id < 0:
            return None

        families = QFontDatabase.applicationFontFamilies(font_id)
        if not families:
            return None
        _font_family = families[0]

    font = app.font()
    font.setFamily(_font_family)
    app.setFont(font)
    return _font_family