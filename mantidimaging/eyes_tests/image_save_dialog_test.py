# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from unittest import mock
from uuid import UUID, uuid4

from typing import NamedTuple
from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


class ImageSaveDialogTest(BaseEyesTest):
    def test_save_dialog_opens_with_no_dataset(self):
        self.imaging.actionSaveImages.trigger()

        self.check_target(widget=self.imaging.image_save_dialog)

    def test_save_dialog_opens_with_dataset(self) -> None:
        TestTuple = NamedTuple('TestTuple', [('id', UUID), ('name', str)])
        stack_list = [TestTuple(uuid4(), 'Test Stack')]
        with mock.patch("mantidimaging.gui.windows.main.MainWindowView.stack_list",
                        new_callable=mock.PropertyMock) as mock_stack_list:
            mock_stack_list.return_value = stack_list
            self.imaging.actionSaveImages.trigger()

        self.check_target(widget=self.imaging.image_save_dialog)
