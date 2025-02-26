# welcome_screen/view_new.py

# Copyright (C) 2025 ISIS Rutherford Appleton Laboratory UKRI
# SPDX-License-Identifier: GPL-3.0-or-later

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap

from mantidimaging.core.utility import finder
from mantidimaging.gui.utility import compile_ui


class WelcomeScreenViewNew(QWidget):
    def __init__(self, parent, presenter):
        super().__init__(parent)
        self.presenter = presenter
        # self.text_container_layout = QVBoxLayout()

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

        self.version_label = QLabel(self)
        # self.text_container.layout().addWidget(self.version_label)

    def set_version_label(self, version_text: str):
        self.version_label.setText(version_text)

    def add_link(self, label: str, row: int) -> None:
        link_label = QLabel(label)
        link_label.setOpenExternalLinks(True)
        print(row)
        self.link_box_layout.addWidget(link_label, row, 0)

        self.link_box_layout.update()
