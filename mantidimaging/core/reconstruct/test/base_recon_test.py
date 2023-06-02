# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

import numpy as np
from parameterized import parameterized

from mantidimaging.core.reconstruct.base_recon import BaseRecon
from mantidimaging.core.utility.data_containers import ReconstructionParameters


class BaseReconTest(unittest.TestCase):

    @parameterized.expand([
        (np.float32, None, 1, 0),
        (np.float32, [1, 1, 1, 1], 2, -0.474886),
        (np.float64, [1, 1, 1, 1], 2, -0.474886),
        (np.float32, [1, 2, 3, 4], 2, -0.826249),
    ])
    def test_prepare_recon_bhc(self, dtype, coefs, input, output):
        data = np.zeros([10, 10], dtype=dtype) + input
        recon_params = mock.create_autospec(ReconstructionParameters)
        recon_params.beam_hardening_coefs = coefs

        result = BaseRecon.prepare_sinogram(data, recon_params)

        self.assertEqual(data.shape, result.shape)
        self.assertEqual(data.dtype, result.dtype)
        self.assertAlmostEqual(output, result[0, 0], 4)
