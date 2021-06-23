# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from unittest import mock

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest, NEXUS_SAMPLE


class LoadDialogTest(BaseEyesTest):
    def test_load_dialog_opens(self):
        self.imaging.actionLoadNeXusFile.trigger()

        self.check_target(widget=self.imaging.nexus_load_dialog)

    def test_load_dialog_selected_dataset(self):
        self.imaging.actionLoadNeXusFile.trigger()
        self.imaging.nexus_load_dialog.view.filePathLineEdit.text = mock.MagicMock(return_value=NEXUS_SAMPLE)

        self.imaging.nexus_load_dialog.scan_nexus_file()
        self.imaging.presenter.load_nexus_file()

        self.check_target(widget=self.imaging.nexus_load_dialog)
