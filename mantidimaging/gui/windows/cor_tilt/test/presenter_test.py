from __future__ import (absolute_import, division, print_function)

import unittest

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.windows.cor_tilt import (
        CORTiltWindowView, CORTiltWindowPresenter)
from mantidimaging.gui.windows.stack_visualiser import (
        StackVisualiserView, StackVisualiserPresenter)

mock = import_mock()


class CORTiltWindowPresenterTest(unittest.TestCase):

    def setUp(self):
        # Mock view
        self.view = mock.create_autospec(CORTiltWindowView)

        self.presenter = CORTiltWindowPresenter(self.view, None)

        # Mock stack
        self.stack = mock.create_autospec(StackVisualiserView)
        data = Images(
                sample=np.ndarray(shape=(128, 10, 128), dtype=np.float32))
        self.stack.presenter = StackVisualiserPresenter(self.stack, data, 0)

    def test_data_selected(self):
        self.presenter.set_stack(self.stack)

        self.view.update_image_preview.assert_called_once()

    def test_set_preview_index(self):
        self.presenter.set_stack(self.stack)

        self.presenter.set_preview_idx(5)
        self.assertEquals(self.presenter.model.preview_idx, 5)
