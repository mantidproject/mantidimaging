# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from collections import namedtuple
from unittest import mock

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


class NexusSaveDialogTest(BaseEyesTest):
    def test_save_dialog_opens_with_dataset(self):
        TestTuple = namedtuple('TestTuple', ['id', 'name'])
        dataset_list = [TestTuple('', 'Test Dataset')]
        with mock.patch("mantidimaging.gui.windows.main.MainWindowView.strict_dataset_list",
                        new_callable=mock.PropertyMock) as mock_dataset_list:
            mock_dataset_list.return_value = dataset_list
            self.imaging.actionSaveNeXusFile.trigger()

        self.check_target(widget=self.imaging.nexus_save_dialog)
