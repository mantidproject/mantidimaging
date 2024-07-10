# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from mantidimaging.core.utility import finder
from PyQt5.QtWidgets import QLabel

from mantidimaging.gui.mvp_base import BaseDialogView


class WelcomeScreenView(BaseDialogView):

    def __init__(self, parent, presenter):
        super().__init__(parent, "gui/ui/welcome_screen_dialog.ui")

        # The background image URL must use forward slashes on both Windows and Linux
        bg_image = finder.ROOT_PATH.replace('\\', '/') + '/gui/ui/images/welcome_screen_background.png'
        self.setStyleSheet("#WelcomeScreenDialog {"
                           f"border-image:url({bg_image});"
                           "min-width:30em; min-height:20em;max-width:30em; max-height:20em;}")
        self.presenter = presenter

        self.issue_box.setVisible(False)

        self.show_at_start.stateChanged.connect(presenter.show_at_start_changed)
        self.ok_button.clicked.connect(self.close)

    def get_show_at_start(self) -> None:
        return self.show_at_start.isChecked()

    def set_show_at_start(self, checked: bool) -> None:
        self.show_at_start.setChecked(checked)

    def set_version_label(self, contents: str) -> None:
        self.version_label.setText(contents)

    def add_link(self, label: str, row: int) -> None:
        link_label = QLabel(label)
        link_label.setOpenExternalLinks(True)
        self.link_box_layout.addWidget(link_label, row, 0)

    def add_issues(self, contents: str) -> None:
        self.issue_box.setVisible(True)
        issues_label = QLabel(contents)
        issues_label.setOpenExternalLinks(True)
        self.issue_box_layout.addWidget(issues_label)
