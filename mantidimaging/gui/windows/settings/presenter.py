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
        self.current_menu_font_size = settings.value('extra_style')['font_size']

    def set_theme(self):
        self.current_theme = self.view.current_theme
        settings.setValue('theme_selection', self.current_theme)
        if self.current_theme == 'Fusion':
            self.view.darkModeCheckBox.setEnabled(True)
        else:
            self.view.darkModeCheckBox.setEnabled(False)
        self.main_window.presenter.do_update_UI()

    def set_extra_style(self):
        extra_style = settings.value('extra_style')
        extra_style.update({'font_size': self.view.current_menu_font_size + 'px'})
        settings.setValue('extra_style', extra_style)
        self.main_window.presenter.do_update_UI()

    def set_dark_mode(self):
        if self.view.darkModeCheckBox.isChecked():
            use_dark_mode = 1
        else:
            use_dark_mode = 0

        settings.setValue('use_dark_mode', use_dark_mode)
        settings.setValue('override_os_theme', True)
        self.main_window.presenter.do_update_UI()
