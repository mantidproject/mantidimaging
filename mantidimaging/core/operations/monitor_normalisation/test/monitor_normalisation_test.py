# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from functools import partial
from unittest import mock

import numpy as np
import numpy.testing as npt

from mantidimaging.core.utility.data_containers import Counts
from mantidimaging.test_helpers.unit_test_helper import generate_images, assert_not_equals
from ..monitor_normalisation import MonitorNormalisation


class MonitorNormalisationTest(unittest.TestCase):

    def test_one_projection(self):
        images = generate_images((1, 1, 1))
        images._log_file = mock.Mock()
        images._log_file.counts = mock.Mock(return_value=Counts(np.sin(np.linspace(0, 1, images.num_projections))))
        self.assertRaises(RuntimeError, MonitorNormalisation.filter_func, images)

    def test_no_counts(self):
        images = generate_images((2, 2, 2))
        images._log_file = mock.Mock()
        images._log_file.counts = mock.Mock(return_value=None)
        self.assertRaises(RuntimeError, MonitorNormalisation.filter_func, images)

    def test_execute(self):
        images = generate_images()
        images._log_file = mock.Mock()
        images._log_file.counts = mock.Mock(return_value=Counts(np.sin(np.linspace(0, 1, images.num_projections))))

        original = images.copy()
        MonitorNormalisation.filter_func(images)
        images._log_file.counts.assert_called_once()
        self.assertEqual(original.data.shape, original.data.shape)
        assert_not_equals(original.data, images.data)

    def test_execute2(self):
        """
        Test that the counts are correctly divided by the value at counts[0].

        In this test that will make all the counts equal to 1, and the data will remain unchanged
        """
        images = generate_images()
        images._log_file = mock.Mock()
        images._log_file.counts = mock.Mock(return_value=Counts(np.full((10, ), 10)))

        original = images.copy()
        MonitorNormalisation.filter_func(images)
        images._log_file.counts.assert_called_once()
        npt.assert_equal(original.data, images.data)

    def test_register_gui(self):
        self.assertEqual(MonitorNormalisation.register_gui(None, None, None), {})

    def test_execute_wrapper(self):
        wrapper = MonitorNormalisation.execute_wrapper()
        self.assertIsNotNone(wrapper)
        self.assertIsInstance(wrapper, partial)
