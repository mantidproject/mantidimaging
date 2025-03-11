# welcome_screen/view.py

# Copyright (C) 2025 ISIS Rutherford Appleton Laboratory UKRI
# SPDX-License-Identifier: GPL-3.0-or-later

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtGui import QPixmap

from mantidimaging.core.utility import finder
from mantidimaging.gui.utility import compile_ui


class WelcomeScreenView(QWidget):
    def __init__(self, parent, presenter):
        super().__init__(parent)
        self.presenter = presenter

        compile_ui("gui/ui/welcome_widget.ui", self)

        if not self.Banner_container.layout():
            self.Banner_container.setLayout(QVBoxLayout())

        # Set the banner image
        banner = finder.ROOT_PATH.replace('\\', '/') + '/gui/ui/images/welcome_banner.png'
        self.banner_label = QLabel(self)
        self.banner_label.setPixmap(QPixmap(banner))
        self.banner_label.setScaledContents(True)
        self.banner_label.setMinimumSize(self.Banner_container.size())
        self.Banner_container.layout().addWidget(self.banner_label)

        self.version_label.setStyleSheet("QLabel { font-size: 10px; }")

    def set_version_label(self, version_text: str):
        self.version_label.setText(version_text)
        self.version_label.setStyleSheet("QLabel { font-size: 18px; margin-left: 5px; }")

    def add_link(self, label: str, row: int) -> None:
        link_label = QLabel()
        link_label.setTextFormat(Qt.RichText)
        link_label.setText(label)
        link_label.setOpenExternalLinks(True)

        link_label.setStyleSheet("QLabel { font-size: 18px; margin-left: 5px; }")
        print("link row: ", row)
        self.link_box_layout.addWidget(link_label, row, 0, Qt.AlignLeft)
        self.link_box_layout.update()

    def add_issues(self, issues_text: str) -> None:
        issues_label = QLabel(issues_text)
        issues_label.setWordWrap(True)
        issues_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

        next_row = self.link_box_layout.rowCount()
        print("issue row: ", next_row)
        self.link_box_layout.addWidget(issues_label, next_row + 1, 0, Qt.AlignLeft)

        print(issues_text)
