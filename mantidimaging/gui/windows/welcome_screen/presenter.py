# Copyright (C) 2025 ISIS Rutherford
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from logging import getLogger

from PyQt5.QtCore import QSettings

from mantidimaging.core.utility import cuda_check
from mantidimaging.gui.windows.welcome_screen.view import WelcomeScreenView
from mantidimaging.core.utility.version_check import versions

LOG = getLogger(__name__)

WELCOME_LINKS = [
    ["Homepage", "https://github.com/mantidproject/mantidimaging"],
    ["Documentation", "https://mantidproject.github.io/mantidimaging/index.html"],
    ["Troubleshooting", "https://mantidproject.github.io/mantidimaging/troubleshooting.html"]
]


class WelcomeScreenPresenter():
    def __init__(self, parent=None):
        self.view = WelcomeScreenView(parent, self)
        self.settings = QSettings()
        self.link_count = 0

        self.do_set_up()

    def do_set_up(self) -> None:
        self.view.set_version_label(f"Mantid Imaging {versions.get_version()}")
        self.set_up_links()
        self.check_issues()

    def show(self) -> None:
        self.view.show()

    def set_up_links(self) -> None:
        use_dark_mode = self.settings.value('use_dark_mode', 'False')
        for link_name, url in WELCOME_LINKS:
            if use_dark_mode == 'True':
                color = '#f7f0f7'
            else:
                color = '#00008B'

            rich_text = (
                f'<a href="{url}" '
                f'style="color: {color} !important; text-decoration: underline !important;">'
                f'{link_name}'
                '</a>'
            )
            self.add_link(rich_text)

    def add_link(self, rich_text: str) -> None:
        self.view.add_link(rich_text, self.link_count)
        self.link_count += 1

    def recolor_links(self):
        """
        Removes existing link labels and re-adds them with the new theme color logic.
        """
        layout = self.view.link_box_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.link_count = 0
        self.set_up_links()

    def check_issues(self) -> None:
        issues = []
        if versions.needs_update():
            msg, detailed = versions.conda_update_message()
            issues.append(msg)
            LOG.info(detailed)

        if not cuda_check.CudaChecker().cuda_is_present():
            msg, detailed = cuda_check.not_found_message()
            issues.append(msg)
            LOG.info(detailed)

        if issues:
            self.view.add_issues("\n".join(issues))
