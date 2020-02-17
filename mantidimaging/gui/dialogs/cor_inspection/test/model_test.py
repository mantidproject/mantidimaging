import unittest

import numpy as np
import numpy.testing as npt

from mantidimaging.gui.dialogs.cor_inspection import (CORInspectionDialogModel, ImageType)


class CORInspectionDialogModelTest(unittest.TestCase):
    def test_construct_from_sinogram(self):
        sino = np.ones(shape=(128, 64), dtype=np.float32)
        m = CORInspectionDialogModel(sino)
        npt.assert_equal(m.sino, sino)
        self.assertEquals(m.cor_extents, (0, 63))
        self.assertEquals(m.proj_angles.shape, (128, ))

    def test_construct_from_projections(self):
        proj = np.ones(shape=(128, 64, 64), dtype=np.float32)
        m = CORInspectionDialogModel(proj, slice_idx=5)
        self.assertEquals(m.sino.shape, (128, 64))
        self.assertEquals(m.cor_extents, (0, 63))
        self.assertEquals(m.proj_angles.shape, (128, ))

    def test_construct_from_sinogram_defaults(self):
        sino = np.ones(shape=(128, 64), dtype=np.float32)
        m = CORInspectionDialogModel(sino)
        self.assertEquals(m.centre_cor, (64 - 1) / 2)

    def test_current_cor(self):
        sino = np.ones(shape=(128, 64), dtype=np.float32)
        m = CORInspectionDialogModel(sino)
        m.centre_cor = 30
        m.cor_step = 10
        self.assertEquals(m.cor(ImageType.LESS), 20)
        self.assertEquals(m.cor(ImageType.CURRENT), 30)
        self.assertEquals(m.cor(ImageType.MORE), 40)

    def test_adjust_cor(self):
        sino = np.ones(shape=(128, 64), dtype=np.float32)
        m = CORInspectionDialogModel(sino)
        m.centre_cor = 30
        m.cor_step = 10

        m.adjust_cor(ImageType.CURRENT)
        self.assertEquals(m.centre_cor, 30)
        self.assertEquals(m.cor_step, 5)

        m.adjust_cor(ImageType.LESS)
        self.assertEquals(m.centre_cor, 25)
        self.assertEquals(m.cor_step, 5)

        m.adjust_cor(ImageType.CURRENT)
        self.assertEquals(m.centre_cor, 25)
        self.assertEquals(m.cor_step, 2.5)

        m.adjust_cor(ImageType.MORE)
        self.assertEquals(m.centre_cor, 27.5)
        self.assertEquals(m.cor_step, 2.5)

        m.adjust_cor(ImageType.CURRENT)
        self.assertEquals(m.centre_cor, 27.5)
        self.assertEquals(m.cor_step, 1.25)
