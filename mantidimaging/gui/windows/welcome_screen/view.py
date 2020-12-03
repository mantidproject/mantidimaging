# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from PyQt5.QtWidgets import QLabel

from mantidimaging.gui.mvp_base import BaseDialogView


class WelcomeScreenView(BaseDialogView):
    def __init__(self, parent, presenter):
        super(WelcomeScreenView, self).__init__(parent, "gui/ui/welcome_screen_dialog.ui")
        self.presenter = presenter

        self.show_at_start.stateChanged.connect(presenter.show_at_start_changed)

    def get_show_at_start(self):
        return self.show_at_start.isChecked()

    def set_show_at_start(self, checked):
        self.show_at_start.setChecked(checked)

    def set_version_label(self, contents):
        self.version_label.setText(contents)

    def add_link(self, label, row):
        link_label = QLabel(label)
        link_label.setOpenExternalLinks(True)
        self.link_box_layout.addWidget(link_label, 0, row)
