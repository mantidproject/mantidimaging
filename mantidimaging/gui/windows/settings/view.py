# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from logging import getLogger
from typing import TYPE_CHECKING

from PyQt5.QtCore import QSettings, QSignalBlocker
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QLineEdit, QPushButton, QFileDialog,
                             QComboBox, QWidget, QTabWidget, QSpinBox)

from mantidimaging.gui.mvp_base import BaseMainWindowView

from qt_material import list_themes, QtStyleTools

from mantidimaging.gui.windows.settings.presenter import SettingsWindowPresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover

LOG = getLogger(__name__)

settings = QSettings('mantidproject', 'Mantid Imaging')


class SettingsWindowView(BaseMainWindowView, QtStyleTools):
    settingsTabWidget: QTabWidget
    appearanceTab: QWidget
    themeName: QComboBox
    themeLabel: QLabel
    menuFontSizeLabel: QLabel
    menuFontSizeChoice: QComboBox
    darkModeCheckBox: QCheckBox
    osDefaultsCheckBox: QCheckBox

    processesLabel: QLabel
    processesSpinBox: QSpinBox

    def __init__(self, main_window: MainWindowView):
        super().__init__(None, 'gui/ui/settings_window.ui')
        self.setWindowTitle('Settings')
        self.main_window = main_window
        self.presenter = SettingsWindowPresenter(self, main_window)
        self._create_logging_tab()

        self.themeName.addItem('Fusion')
        self.themeName.addItems(list_themes())
        self.themeName.setCurrentText(self.presenter.current_theme)

        self.menuFontSizeChoice.addItems([str(font_size) for font_size in range(4, 21)])
        self.menuFontSizeChoice.setCurrentText(self.presenter.current_menu_font_size.replace('px', ''))

        self.themeName.currentTextChanged.connect(self.presenter.set_theme)
        self.menuFontSizeChoice.currentTextChanged.connect(self.presenter.set_extra_style)
        self.darkModeCheckBox.stateChanged.connect(self.presenter.set_dark_mode)
        self.osDefaultsCheckBox.stateChanged.connect(self.presenter.set_to_os_defaults)

        if self.current_theme != 'Fusion':
            self.darkModeCheckBox.setEnabled(False)
        with (QSignalBlocker(self.darkModeCheckBox)):
            if settings.value('use_dark_mode') == 'True' or (settings.value('os_theme') == 'Dark'
                                                             and settings.value('override_os_theme') == 'False'):
                self.darkModeCheckBox.setChecked(True)
            else:
                self.darkModeCheckBox.setChecked(False)

        if settings.value('use_os_defaults') == 'True' or settings.value('use_os_defaults') is None:
            self.osDefaultsCheckBox.setChecked(True)
        self.processesSpinBox.setMinimum(1)
        self.processesSpinBox.setMaximum(128)
        self.processesSpinBox.setValue(settings.value("multiprocessing/process_count", 8, type=int))
        self.processesSpinBox.valueChanged.connect(self.presenter.set_processes_value)

    def _create_logging_tab(self):
        settings = QSettings()

        self.loggingTab = QWidget()
        self.settingsTabWidget.addTab(self.loggingTab, "Logging")

        # Create main
        mainLayout = QVBoxLayout()
        self.loggingTab.setLayout(mainLayout)

        # Log Directory
        dirLayout = QHBoxLayout()
        self.logDirectoryLabel = QLabel("Log Directory:")
        self.logDirectoryLineEdit = QLineEdit(settings.value("logging/log_dir", "", type=str))
        self.logDirectoryLineEdit.setFixedWidth(200)
        self.logDirectoryButton = QPushButton("Browse")
        self.logDirectoryButton.setFixedWidth(80)
        self.logDirectoryButton.clicked.connect(self.select_log_directory)
        dirLayout.addWidget(self.logDirectoryLabel)
        dirLayout.addWidget(self.logDirectoryLineEdit)
        dirLayout.addWidget(self.logDirectoryButton)
        dirLayout.addStretch()
        mainLayout.addLayout(dirLayout)

        # Log Level
        levelLayout = QHBoxLayout()
        self.logLevelLabel = QLabel("Log Level:")
        self.logLevelComboBox = QComboBox()
        self.logLevelComboBox.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.logLevelComboBox.setCurrentText(settings.value("logging/log_level", "INFO"))
        self.logLevelComboBox.setFixedWidth(150)
        levelLayout.addWidget(self.logLevelLabel)
        levelLayout.addWidget(self.logLevelComboBox)
        levelLayout.addStretch()
        mainLayout.addLayout(levelLayout)

        # Retention (days)
        retentionLayout = QHBoxLayout()
        self.logRetentionLabel = QLabel("Retention (days):")
        self.logRetentionSpinBox = QSpinBox()
        self.logRetentionSpinBox.setMinimum(1)
        self.logRetentionSpinBox.setMaximum(365)
        self.logRetentionSpinBox.setValue(settings.value("logging/retention", 30, type=int))
        self.logRetentionSpinBox.setFixedWidth(80)
        retentionLayout.addWidget(self.logRetentionLabel)
        retentionLayout.addWidget(self.logRetentionSpinBox)
        retentionLayout.addStretch()
        mainLayout.addLayout(retentionLayout)

        # Performance
        self.performanceLoggingCheckBox = QCheckBox("Performance Logging")
        self.performanceLoggingCheckBox.setChecked(settings.value("logging/performance_log", False, type=bool))
        mainLayout.addWidget(self.performanceLoggingCheckBox)

        # align
        mainLayout.addStretch()

        # Connect signals
        self.logLevelComboBox.currentTextChanged.connect(self.presenter.set_log_level)
        self.logRetentionSpinBox.valueChanged.connect(self.presenter.set_log_retention)
        self.logDirectoryButton.clicked.connect(self.select_log_directory)
        self.performanceLoggingCheckBox.stateChanged.connect(self.presenter.set_performance_logging)

    def select_log_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Log Directory")
        if directory:
            self.logDirectoryLineEdit.setText(directory)
            self.presenter.set_log_directory(directory)

    @property
    def current_theme(self) -> str:
        return self.themeName.currentText()

    @property
    def current_menu_font_size(self) -> str:
        return self.menuFontSizeChoice.currentText()

    @property
    def current_processes_value(self) -> int:
        return self.processesSpinBox.value()
