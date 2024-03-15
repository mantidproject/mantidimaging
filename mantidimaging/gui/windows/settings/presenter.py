# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from PyQt5.QtCore import QSettings

from mantidimaging.gui.mvp_base import BasePresenter

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from mantidimaging.gui.windows.settings.view import SettingsWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main import MainWindowView

settings = QSettings('mantidproject', 'Mantid Imaging')


class SettingsWindowPresenter(BasePresenter):
    view: 'SettingsWindowView'

    def __init__(self, view: 'SettingsWindowView', main_window: 'MainWindowView'):
        super().__init__(view)
        self.view = view
        self.main_window = main_window
        self.current_theme = settings.value('theme_selection')

    def set_theme(self):
        self.current_theme = self.view.current_theme
        settings.setValue('theme_selection', self.current_theme)
        self.main_window.set_theme(self.current_theme)
