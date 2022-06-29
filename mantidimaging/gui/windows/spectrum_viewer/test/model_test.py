# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock
from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowPresenter, SpectrumViewerWindowModel
from mantidimaging.test_helpers.unit_test_helper import generate_images


class SpectrumViewerWindowPresenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.presenter = mock.create_autospec(SpectrumViewerWindowPresenter)
        self.model = SpectrumViewerWindowModel(self.presenter)

    def test_set_stacks(self):
        stack = generate_images([10, 11, 12])
        open_stack = generate_images([10, 11, 12])
        self.model.set_stack(stack)
        self.model.set_open_stack(open_stack)

        self.assertEqual(self.model._stack, stack)
        self.assertEqual(self.model._open_stack, open_stack)
        self.assertEqual(self.model.tof_range, (0, 9))
