from __future__ import (absolute_import, division, print_function)

import unittest

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.dialogs.cor_tilt import CORTiltDialogModel
from mantidimaging.gui.windows.stack_visualiser import (
        StackVisualiserView, StackVisualiserPresenter)

mock = import_mock()


class CORTiltDialogModelTest(unittest.TestCase):

    def setUp(self):
        self.model = CORTiltDialogModel()

        # Mock stack
        self.stack = mock.create_autospec(StackVisualiserView)
        data = Images(
                sample=np.ndarray(shape=(10, 128, 128), dtype=np.float32))
        self.stack.presenter = StackVisualiserPresenter(self.stack, data, 0)

        self.model.initial_select_data(self.stack)

    def test_empty_init(self):
        m = CORTiltDialogModel()
        self.assertIsNone(m.stack)
        self.assertIsNone(m.sample)

    def test_init(self):
        self.assertEquals(self.model.sample.shape, (10, 128, 128))
        self.assertEquals(self.model.num_projections, 10)

    def test_calculate_slices(self):
        self.assertIsNone(self.model.slice_indices)
        self.model.roi = (30, 25, 100, 120)
        self.model.calculate_slices(5)
        self.assertEquals(self.model.slice_indices.shape, (5, ))

    def test_calculate_slices_no_roi(self):
        self.assertIsNone(self.model.slice_indices)
        self.model.roi = None
        self.model.calculate_slices(5)
        self.assertIsNone(self.model.slice_indices)

    def test_tilt_line_data(self):
        self.model.slice_indices = np.array([50, 40, 30, 20])
        self.model.cors = np.array([1, 2, 3, 4])
        self.model.cor = 1

        data = self.model.preview_tilt_line_data

        self.assertEquals(data, ([1, 4], [50, 20]))

    def test_fit_y_data(self):
        self.model.slices = np.array([1, 2, 3])
        self.model.cor = 1
        self.model.m = 2

        data = self.model.preview_fit_y_data

        self.assertEquals(data, [3, 5, 7])
