# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from unittest import mock

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.io.instrument_log import InstrumentLog, LogColumn
from mantidimaging.core.operations.append_stacks import AppendStacks
from mantidimaging.core.utility.data_containers import ProjectionAngles
from mantidimaging.test_helpers.start_qapplication import start_multiprocessing_pool


@start_multiprocessing_pool
class AppendStacksTest(unittest.TestCase):
    """
    Test append stacks filter.
    """

    def test_append_stacks_not_ordered_no_angles(self):
        images = th.generate_images()
        images_to_append = th.generate_images()
        result = AppendStacks().filter_func(images.copy(),
                                            "Tomography",
                                            images_to_append.copy(),
                                            False)

        npt.assert_array_equal(images.data, result.data[0:images.num_images])
        npt.assert_array_equal(images_to_append.data, result.data[-images_to_append.num_images:])

    def test_append_stacks_ordered(self):
        images = th.generate_images()
        images_to_append = th.generate_images()
        images_num = images.num_images

        mock_log_data = mock.create_autospec(InstrumentLog, instance=True)
        mock_log_data.has_projection_angles.return_value = True
        angles = np.arange(0, images.num_projections * 2, 2)
        mock_log_data.projection_angles.return_value = ProjectionAngles(np.deg2rad(angles))
        mock_log_data.source_file = "foo"
        mock_log_data.data = {LogColumn.PROJECTION_ANGLE: angles.tolist()}
        mock_log_data.get_column.return_value = angles.tolist()

        mock_log_data_to_append = mock.create_autospec(InstrumentLog, instance=True)
        mock_log_data_to_append.has_projection_angles.return_value = True
        angles_to_append = np.arange(1, 1 + images.num_projections * 2, 2)
        mock_log_data_to_append.projection_angles.return_value = ProjectionAngles(np.deg2rad(angles_to_append))
        mock_log_data_to_append.source_file = "bar"
        mock_log_data_to_append.data = {LogColumn.PROJECTION_ANGLE: angles_to_append.tolist()}
        mock_log_data_to_append.get_column.return_value = angles_to_append.tolist()

        images.log_file = mock_log_data
        images_to_append.log_file = mock_log_data_to_append

        result = AppendStacks().filter_func(images,
                                            "Tomography",
                                            images_to_append,
                                            True)
        expected_result = np.concatenate((np.deg2rad(angles), np.deg2rad(angles_to_append)))

        expected_ind_order = expected_result.argsort()

        npt.assert_array_almost_equal(expected_result[expected_ind_order], result.projection_angles().value)


