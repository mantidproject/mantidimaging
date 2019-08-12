import unittest

import numpy as np

from mantidimaging.core.data import Images


from mantidimaging.gui.windows.tomopy_recon import TomopyReconWindowModel
from mantidimaging.gui.windows.stack_visualiser import (
        StackVisualiserView, StackVisualiserPresenter)

import mock


class TomopyReconWindowModelTest(unittest.TestCase):

    def setUp(self):
        self.model = TomopyReconWindowModel()

        # Mock stack
        self.stack = mock.create_autospec(StackVisualiserView)
        data = Images(
                sample=np.ndarray(shape=(128, 10, 128), dtype=np.float32))
        self.stack.presenter = StackVisualiserPresenter(self.stack, data)

        self.model.initial_select_data(self.stack)

    def test_empty_init(self):
        m = TomopyReconWindowModel()
        self.assertIsNone(m.sample)
        self.assertIsNone(m.projection)

    def test_projection_generate(self):
        self.assertIsNotNone(self.model.projection)
        self.assertEquals(self.model.projection.shape, (10, 128, 128))

    def test_generate_cors(self):
        self.assertIsNone(self.model.cors)
        self.model.generate_cors(500, 0)
        self.assertEquals(self.model.cors.shape, (128, ))

    def test_generate_projection_angles(self):
        self.assertIsNone(self.model.projection_angles)
        self.model.generate_projection_angles(360)
        self.assertEquals(self.model.projection_angles.shape, (10, ))
