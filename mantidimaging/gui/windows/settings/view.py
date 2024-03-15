# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from logging import getLogger
from typing import TYPE_CHECKING

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QTabWidget, QWidget, QComboBox, QLabel

from mantidimaging.gui.mvp_base import BaseMainWindowView

from qt_material import list_themes

from mantidimaging.gui.windows.settings.presenter import SettingsWindowPresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover

LOG = getLogger(__name__)

settings = QSettings('mantidproject', 'Mantid Imaging')


class SettingsWindowView(BaseMainWindowView):
    settingsTabWidget: QTabWidget
    appearanceTab: QWidget
    themeName: QComboBox
    themeLabel: QLabel

    def __init__(self, main_window: 'MainWindowView'):
        super().__init__(None, 'gui/ui/settings_window.ui')
        self.setWindowTitle('Settings')
        self.main_window = main_window
        self.presenter = SettingsWindowPresenter(self, main_window)

        self.themeName.addItem('Fusion')
        self.themeName.addItems(list_themes())
        self.themeName.setCurrentText(self.presenter.current_theme)

        self.themeName.currentTextChanged.connect(self.presenter.set_theme)

    @property
    def current_theme(self) -> str:
        return self.themeName.currentText()
