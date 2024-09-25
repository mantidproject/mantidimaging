# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from unittest import mock

from mantidimaging.core.data.dataset import Dataset
from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


class NexusSaveDialogTest(BaseEyesTest):

    def test_save_dialog_opens_with_dataset(self):
        with mock.patch("mantidimaging.gui.windows.main.MainWindowPresenter.datasets",
                        new_callable=mock.PropertyMock) as mock_datasets:
            mock_datasets.return_value = [Dataset(name='Test Dataset')]
            self.imaging.actionSaveNeXusFile.trigger()

        self.check_target(widget=self.imaging.nexus_save_dialog)
