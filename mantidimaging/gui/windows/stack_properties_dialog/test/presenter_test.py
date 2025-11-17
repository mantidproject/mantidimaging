# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

from mantidimaging.gui.windows.stack_properties_dialog.presenter import StackPropertiesPresenter
from mantidimaging.gui.windows.stack_properties_dialog.view import StackPropertiesDialog


class StackPropertiesPresenterTest(unittest.TestCase):

    def setUp(self):
        self.view = mock.Mock(spec=StackPropertiesDialog)
        self.view.parent_view = mock.Mock()
        self.presenter = StackPropertiesPresenter(self.view)
        self.view.datasetSelector = mock.Mock()
        self.view.originDatasetName = mock.Mock()
        self.view.destinationTypeComboBox = mock.Mock()
        self.view.originDataType = mock.Mock()
        self.view.stack = mock.Mock()

    def test_WHEN_set_stack_data_THEN_stack_data_set_correctly(self):
        self.view.stack.data = np.ones([3, 11, 12])
        self.view.stack.shape = self.view.stack.data.shape
        self.view.stack.dtype = self.view.stack.data.dtype
        self.view.stack.filenames = ["test/filename/a.tif", "test/filename/b.tif", "test/filename/c.tif"]
        self.presenter.get_stack_size_MB = mock.Mock()
        self.presenter.get_stack_size_MB.return_value = 10
        self.presenter.set_stack_data()
        self.presenter.set_stack_directory()

        self.assertEqual(self.view.directory, Path("test/filename/"))
        self.assertEqual(self.view.stack_shape, (3, 11, 12))
