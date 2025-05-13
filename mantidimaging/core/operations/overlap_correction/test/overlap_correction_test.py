# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from functools import partial
from unittest import mock

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.overlap_correction import OverlapCorrection
from mantidimaging.core.operations.overlap_correction.overlap_correction import ShutterInfo
from mantidimaging.test_helpers.start_qapplication import start_multiprocessing_pool


@start_multiprocessing_pool
class OverlapCorrectionTest(unittest.TestCase):

    def test_WHEN_no_shutter_file_THEN_exception(self):
        images = th.generate_images()
        images._shutter_count_file = None

        self.assertRaises(RuntimeError, OverlapCorrection.filter_func, images)

    def test_executed_par(self):
        self.do_execute(True)

    def test_executed_seq(self):
        self.do_execute(False)

    @mock.patch('mantidimaging.core.operations.overlap_correction.overlap_correction.OverlapCorrection.get_shutters')
    def do_execute(self, in_parallel, get_shutters_mock):
        # only works on square images
        if in_parallel:
            images = th.generate_images_for_parallel((15, 15, 15))
        else:
            images = th.generate_images((10, 10, 10))

        images._shutter_count_file = mock.Mock()
        get_shutters_mock.return_value = [
            ShutterInfo(0, 102, start_index=0, end_index=2),
            ShutterInfo(1, 230, start_index=2, end_index=4),
            ShutterInfo(2, 235, start_index=4, end_index=10)
        ]

        original = images.copy()
        images = OverlapCorrection.filter_func(images)

        get_shutters_mock.assert_called_once()
        th.assert_not_equals(original.data, images.data)

    def test_register_gui(self):
        assert OverlapCorrection.register_gui(None, None, None) == {}

    def test_execute_wrapper(self):
        wrapper = OverlapCorrection.execute_wrapper()
        assert wrapper is not None
        assert isinstance(wrapper, partial)

    def test_validate_execute_kwargs(self):
        assert OverlapCorrection.validate_execute_kwargs({}) is True
