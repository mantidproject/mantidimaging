# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtGui import QPixmap, QIcon

from mantidimaging.core.utility import finder
from mantidimaging.gui.utility import compile_ui


class CloseButton(QPushButton):
    """Custom Close Button with hover effect"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.default_icon = QIcon(finder.ROOT_PATH + "/gui/ui/images/x_button.png")
        self.hover_icon = QIcon(finder.ROOT_PATH + "/gui/ui/images/x_button_hover.png")

        self.setIcon(self.default_icon)
        self.setIconSize(QSize(20, 20))
        self.setFixedSize(25, 25)
        self.setStyleSheet("background: transparent; border: none;")

    def enterEvent(self, event):
        """Change icon when hovering over the button"""
        self.setIcon(self.hover_icon)

    def leaveEvent(self, event):
        """Revert icon when mouse leaves the button"""
        self.setIcon(self.default_icon)


class WelcomeScreenView(QWidget):

    closed = pyqtSignal()

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
        self.banner_label.setScaledContents(False)
        self.banner_label.setMinimumSize(self.Banner_container.size())
        self.Banner_container.layout().addWidget(self.banner_label)

        self.close_button = CloseButton(self)

        self.close_button.clicked.connect(self._handle_close_button_clicked)

        # Done to make sure the button appears in the top-right corner after rendering
        QTimer.singleShot(1, self.position_close_button)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_close_button()

    def position_close_button(self):
        self.close_button.move(self.banner_label.width() - self.close_button.width() - 1, 10)

    def close_welcome_screen(self):
        self.parent().close()

    def set_version_label(self, version_text: str):
        self.version_label.setText(version_text)
        self.version_label.setStyleSheet("QLabel { font-size: 18px; margin-left: 5px; }")

    def add_link(self, label: str, row: int) -> None:
        link_label = QLabel()
        link_label.setTextFormat(Qt.RichText)
        link_label.setText(label)
        link_label.setOpenExternalLinks(True)

        link_label.setStyleSheet("QLabel { font-size: 18px; margin-left: 5px; }")
        self.link_box_layout.addWidget(link_label, row, 0, Qt.AlignLeft)
        self.link_box_layout.update()

    def add_issues(self, issues_text: str) -> None:
        self.issues_label.setWordWrap(True)
        self.issues_label.setStyleSheet("QLabel { "
                                        "  color: red; "
                                        "  font-weight: bold; "
                                        "  font-size: 18px; "
                                        "  margin-left: 5px; "
                                        "  margin-top: 5px; "
                                        "}")
        self.issues_label.setText(issues_text)

    def _handle_close_button_clicked(self):
        self.close()
        self.closed.emit()
