# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from PyQt5.QtCore import QSettings

from mantidimaging.gui.mvp_base.presenter import BasePresenter
from mantidimaging.gui.windows.welcome_screen.view import WelcomeScreenView
from mantidimaging import __version__ as version_no

WELCOME_LINKS = [["Homepage", "https://github.com/mantidproject/mantidimaging"]]


class WelcomeScreenPresenter(BasePresenter):
    def __init__(self, parent=None, view=None):
        if view is None:
            view = WelcomeScreenView(parent, self)

        super(WelcomeScreenPresenter, self).__init__(view)
        self.view.set_version_label(f"Mantid Imaging {version_no}")

        self.link_count = 0
        self.set_up_links()

        self.settings = QSettings()

        self.set_up_show_at_start()

    def show(self):
        self.view.show()

    @staticmethod
    def show_at_start_enabled():
        settings = QSettings()
        return settings.value("welcome_screen/show_at_start", defaultValue=True, type=bool)

    def set_up_links(self):
        for link_name, url in WELCOME_LINKS:
            self.add_link(link_name, url)

    def add_link(self, link_name, url):
        rich_text = f'<a href="{url}">{link_name}</a>'
        self.view.add_link(rich_text, self.link_count)
        self.link_count += 1

    def set_up_show_at_start(self):
        show_at_start = WelcomeScreenPresenter.show_at_start_enabled()
        self.view.set_show_at_start(show_at_start)
        self.show_at_start_changed()

    def show_at_start_changed(self):
        show_at_start = self.view.get_show_at_start()
        self.settings.setValue("welcome_screen/show_at_start", show_at_start)
