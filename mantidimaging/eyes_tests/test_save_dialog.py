# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from unittest import mock

from collections import namedtuple
from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


class SaveDialogTest(BaseEyesTest):
    def test_save_dialog_opens_with_no_dataset(self):
        self.imaging.actionSave.trigger()

        self.check_target(widget=self.imaging.save_dialogue)

    def test_save_dialog_opens_with_dataset(self):
        TestTuple = namedtuple('TestTuple', ['id', 'name'])
        type(self.imaging).stack_list = mock.PropertyMock(return_value=[TestTuple('', 'Test Stack')])
        self.imaging.actionSave.trigger()

        self.check_target(widget=self.imaging.save_dialogue)
