# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from PyQt5.QtCore import QSettings, QSignalBlocker

from mantidimaging.gui.mvp_base import BasePresenter

LOG = getLogger(__name__)

if TYPE_CHECKING:
    from mantidimaging.gui.windows.settings.view import SettingsWindowView  # pragma: no cover
    from mantidimaging.gui.windows.main import MainWindowView

settings = QSettings('mantidproject', 'Mantid Imaging')


class SettingsWindowPresenter(BasePresenter):
    view: SettingsWindowView

    def __init__(self, view: SettingsWindowView, main_window: MainWindowView):
        super().__init__(view)
        self.view = view
        self.main_window = main_window
        self.current_theme = settings.value('theme_selection')
        if settings.value('selected_font_size') is None:
            self.current_menu_font_size = settings.value('default_font_size')
        else:
            self.current_menu_font_size = settings.value('selected_font_size')

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
        settings.setValue('selected_font_size', self.view.current_menu_font_size)
        extra_style.update({'font_size': self.view.current_menu_font_size + 'px'})
        settings.setValue('extra_style', extra_style)
        self.main_window.presenter.do_update_UI()

    def set_dark_mode(self):
        if self.view.darkModeCheckBox.isChecked():
            use_dark_mode = 'True'
        else:
            use_dark_mode = 'False'

        settings.setValue('use_dark_mode', use_dark_mode)
        settings.setValue('override_os_theme', 'True')
        self.main_window.presenter.do_update_UI()

    def set_to_os_defaults(self):
        if self.view.osDefaultsCheckBox.isChecked():
            settings.setValue('use_os_defaults', 'True')
            theme_text = 'Fusion'
            theme_enabled = False
            font_text = settings.value('default_font_size')
            font_enabled = False
            if settings.value('os_theme') == 'Dark':
                dark_mode_checked = True
            else:
                dark_mode_checked = False
            dark_mode_enabled = False
        else:
            settings.setValue('use_os_defaults', 'False')
            theme_text = settings.value('theme_selection')
            theme_enabled = True
            font_text = settings.value('selected_font_size')
            font_enabled = True
            if settings.value('use_dark_mode') == 'True':
                dark_mode_checked = True
            else:
                dark_mode_checked = False
            dark_mode_enabled = True
        with QSignalBlocker(self.view.themeName):
            self.view.themeName.setCurrentText(theme_text)
            self.view.themeName.setEnabled(theme_enabled)
        with QSignalBlocker(self.view.menuFontSizeChoice):
            self.view.menuFontSizeChoice.setCurrentText(font_text)
            self.view.menuFontSizeChoice.setEnabled(font_enabled)
        with QSignalBlocker(self.view.darkModeCheckBox):
            self.view.darkModeCheckBox.setChecked(dark_mode_checked)
            self.view.darkModeCheckBox.setEnabled(dark_mode_enabled)
        self.main_window.presenter.do_update_UI()

    def set_processes_value(self):
        settings.setValue('multiprocessing/process_count', self.view.current_processes_value)
