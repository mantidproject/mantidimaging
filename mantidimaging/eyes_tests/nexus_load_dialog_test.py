# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest, NEXUS_SAMPLE


class NexusLoadDialogTest(BaseEyesTest):
    def test_load_dialog_opens(self):
        self.imaging.actionLoadNeXusFile.trigger()

        self.check_target(widget=self.imaging.nexus_load_dialog)

    def test_load_nexus_file_populates_window(self):
        self.imaging.actionLoadNeXusFile.trigger()
        self.imaging.nexus_load_dialog.filePathLineEdit.setText(NEXUS_SAMPLE)

        self.imaging.nexus_load_dialog.presenter.scan_nexus_file()
        self.check_target(widget=self.imaging.nexus_load_dialog)

    def test_load_nexus_file_creates_stack(self):
        self.imaging.actionLoadNeXusFile.trigger()
        self.imaging.nexus_load_dialog.filePathLineEdit.setText(NEXUS_SAMPLE)

        self.imaging.nexus_load_dialog.presenter.scan_nexus_file()
        self.imaging.presenter.load_nexus_file()

        self.check_target(widget=self.imaging)
