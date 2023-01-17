# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import numpy.testing as npt

from mantidimaging.core.utility.data_containers import ScalarCoR, ReconstructionParameters
from mantidimaging.gui.dialogs.cor_inspection import CORInspectionDialogModel
from mantidimaging.gui.dialogs.cor_inspection.model import INIT_ITERS_CENTRE_VALUE, INIT_ITERS_STEP
from mantidimaging.gui.dialogs.cor_inspection.types import ImageType
from mantidimaging.test_helpers.unit_test_helper import generate_images


class CORInspectionDialogModelTest(unittest.TestCase):
    def test_construct(self):
        images = generate_images()
        m = CORInspectionDialogModel(images, 5, ScalarCoR(20), ReconstructionParameters('FBP_CUDA', 'ram-lak'), False)
        npt.assert_equal(m.sino, images.sino(5))
        self.assertEqual(m.cor_extents, (0, 9))
        self.assertEqual(m.proj_angles.value.shape, (10, ))

    def test_start_cor_step(self):
        images = generate_images()
        m = CORInspectionDialogModel(images, 5, ScalarCoR(20), ReconstructionParameters('FBP_CUDA', 'ram-lak'), False)
        self.assertEqual(images.width * 0.05, m.step)

    def test_current_cor(self):
        images = generate_images()
        m = CORInspectionDialogModel(images, 5, ScalarCoR(20), ReconstructionParameters('FBP_CUDA', 'ram-lak'), False)
        m.centre_value = 5
        m.step = 1
        self.assertEqual(m.cor(ImageType.LESS), 4)
        self.assertEqual(m.cor(ImageType.CURRENT), 5)
        self.assertEqual(m.cor(ImageType.MORE), 6)

    def test_adjust_cor(self):
        images = generate_images()
        m = CORInspectionDialogModel(images, 5, ScalarCoR(20), ReconstructionParameters('FBP_CUDA', 'ram-lak'), False)
        m.centre_value = 5
        m.step = 1

        m.adjust(ImageType.CURRENT)
        self.assertEqual(m.centre_value, 5)
        self.assertEqual(m.step, 0.5)

        m.adjust(ImageType.LESS)
        self.assertEqual(m.centre_value, 4.5)
        self.assertEqual(m.step, 0.5)

        m.adjust(ImageType.CURRENT)
        self.assertEqual(m.centre_value, 4.5)
        self.assertEqual(m.step, 0.25)

        m.adjust(ImageType.MORE)
        self.assertEqual(m.centre_value, 4.75)
        self.assertEqual(m.step, 0.25)

        m.adjust(ImageType.CURRENT)
        self.assertEqual(m.centre_value, 4.75)
        self.assertEqual(m.step, 0.125)

    def test_iters_mode_init(self):
        images = generate_images()
        m = CORInspectionDialogModel(images, 5, ScalarCoR(20), ReconstructionParameters('FBP_CUDA', 'ram-lak'), True)

        self.assertEqual(m.centre_value, INIT_ITERS_CENTRE_VALUE)
        self.assertEqual(m.step, INIT_ITERS_STEP)
        self.assertEqual(m._recon_preview, m._recon_iters_preview)
        self.assertEqual(m._divide_step, m._divide_iters_step)

    def test_cor_mode_init(self):
        images = generate_images()
        initial_cor = ScalarCoR(20)
        m = CORInspectionDialogModel(images, 5, initial_cor, ReconstructionParameters('FBP_CUDA', 'ram-lak'), False)

        self.assertEqual(m.centre_value, initial_cor.value)
        self.assertEqual(m.step, images.width * 0.05)
        self.assertEqual(m._recon_preview, m._recon_cor_preview)
        self.assertEqual(m._divide_step, m._divide_cor_step)

    def test_divide_iters_step(self):
        images = generate_images()
        m = CORInspectionDialogModel(images, 5, ScalarCoR(20), ReconstructionParameters('FBP_CUDA', 'ram-lak'), True)
        m.step = 11

        m._divide_step()
        self.assertEqual(m.step, 5)

    def test_iterations(self):
        images = generate_images()
        m = CORInspectionDialogModel(images, 5, ScalarCoR(20), ReconstructionParameters('FBP_CUDA', 'ram-lak'), True)

        m.adjust(ImageType.LESS)
        self.assertEqual(m.centre_value, 50)
        self.assertEqual(m.step, 50)

        m.adjust(ImageType.CURRENT)
        self.assertEqual(m.centre_value, 50)
        self.assertEqual(m.step, 25)

        m.adjust(ImageType.MORE)
        self.assertEqual(m.centre_value, 75)
        self.assertEqual(m.step, 25)

    @patch('mantidimaging.gui.dialogs.cor_inspection.model.replace')
    def test_recon_iters_preview(self, replace_mock):
        images = generate_images()
        m = CORInspectionDialogModel(images, 5, ScalarCoR(20), ReconstructionParameters('FBP_CUDA', 'ram-lak'), True)

        m.reconstructor = Mock()
        m.recon_preview(ImageType.CURRENT)
        replace_mock.assert_called_once_with(m.recon_params, num_iter=100)
        m.reconstructor.single_sino.assert_called_once_with(m.sino, m.initial_cor, m.proj_angles,
                                                            replace_mock.return_value)
