# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import pytest
import unittest
from unittest import mock

import numpy as np

from mantidimaging.core.reconstruct.base_recon import BaseRecon
from mantidimaging.core.utility.data_containers import ReconstructionParameters


class BaseReconTest(unittest.TestCase):
    def test_prepare_recon_no_bhc(self):
        data = np.ones([10, 10], dtype=np.float32)
        recon_params = mock.create_autospec(ReconstructionParameters)
        recon_params.beam_hardening_coefs = None

        result = BaseRecon.prepare_sinogram(data, recon_params)

        self.assertEqual(data.shape, result.shape)
        self.assertEqual(data.dtype, result.dtype)
        self.assertEqual(0, result[0, 0])  # -log(1) == 0

    @pytest.mark.xfail(reason="issue #1748")
    def test_prepare_recon_bhc(self):
        data = np.ones([10, 10], dtype=np.float32) * 2
        recon_params = mock.create_autospec(ReconstructionParameters)
        recon_params.beam_hardening_coefs = [1, 1, 1, 1]

        result = BaseRecon.prepare_sinogram(data, recon_params)

        self.assertEqual(data.shape, result.shape)
        self.assertEqual(data.dtype, result.dtype)
        self.assertAlmostEqual(-0.474886, result[0, 0], 4)
