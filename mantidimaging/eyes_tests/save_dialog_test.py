# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from unittest import mock

from collections import namedtuple
from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


class SaveDialogTest(BaseEyesTest):
    def test_save_dialog_opens_with_no_dataset(self):
        self.imaging.actionSave.trigger()

        self.check_target(widget=self.imaging.save_dialog)

    def test_save_dialog_opens_with_dataset(self):
        TestTuple = namedtuple('TestTuple', ['id', 'name'])
        stack_list = [TestTuple('', 'Test Stack')]
        with mock.patch("mantidimaging.gui.windows.main.MainWindowView.stack_list",
                        new_callable=mock.PropertyMock) as mock_stack_list:
            mock_stack_list.return_value = stack_list
            self.imaging.actionSave.trigger()

        self.check_target(widget=self.imaging.save_dialog)
