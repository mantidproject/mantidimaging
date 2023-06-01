# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest, LOAD_SAMPLE


class ImageLoadDialogTest(BaseEyesTest):

    def test_load_dialog_opens(self):
        self.imaging.actionLoadDataset.trigger()

        self.check_target(widget=self.imaging.image_load_dialog)

    def test_load_dialog_selected_dataset(self):
        self.imaging.actionLoadDataset.trigger()
        self.imaging.image_load_dialog.presenter.do_update_sample(LOAD_SAMPLE)

        self.check_target(widget=self.imaging.image_load_dialog)
