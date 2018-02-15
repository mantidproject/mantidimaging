import unittest

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.windows.tomopy_recon import (
        TomopyReconWindowView, TomopyReconWindowPresenter)
from mantidimaging.gui.windows.stack_visualiser import (
        StackVisualiserView, StackVisualiserPresenter)

mock = import_mock()


class TomopyReconWindowPresenterTest(unittest.TestCase):

    def setUp(self):
        # Mock view
        self.view = mock.create_autospec(TomopyReconWindowView)
        self.view.rotation_centre = 500
        self.view.cor_gradient = 0
        self.view.max_proj_angle = 360

        self.presenter = TomopyReconWindowPresenter(self.view, None)

        # Mock stack
        self.stack = mock.create_autospec(StackVisualiserView)
        data = Images(
                sample=np.ndarray(shape=(128, 10, 128), dtype=np.float32))
        self.stack.presenter = StackVisualiserPresenter(self.stack, data, 0)

    def test_data_selected(self):
        self.presenter.set_stack(self.stack)

        self.view.update_projection_preview.assert_called_once()
        self.view.update_recon_preview.assert_called_once_with(None)
        self.assertEquals(self.view.rotation_centre, 0)
        self.assertEquals(self.view.cor_gradient, 0.0)

    def test_prepare_recon(self):
        self.presenter.set_stack(self.stack)

        self.assertIsNone(self.presenter.model.cors)
        self.assertIsNone(self.presenter.model.projection_angles)

        self.presenter.prepare_reconstruction()

        self.assertIsNotNone(self.presenter.model.cors)
        self.assertIsNotNone(self.presenter.model.projection_angles)

    def test_set_preview_slice_index(self):
        self.presenter.set_stack(self.stack)
        self.view.set_preview_slice_idx.reset_mock()

        self.presenter.set_preview_slice_idx(5)
        self.assertEquals(self.presenter.model.preview_slice_idx, 5)
        self.view.set_preview_slice_idx.assert_called_once_with(5)
