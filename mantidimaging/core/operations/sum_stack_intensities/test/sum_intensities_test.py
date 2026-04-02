# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations
import unittest
import numpy as np
import numpy.testing as npt
from parameterized import parameterized

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.sum_stack_intensities.sum_intensities import SumIntensitiesFilter
from mantidimaging.core.utility.data_containers import ProjectionAngles


class SumIntensitiesTest(unittest.TestCase):
    """Unit tests for the SumIntensitiesFilter class."""

    def setUp(self):
        self.primary = th.generate_images()
        self.secondary = th.generate_images()

    def _make_projection_angles(self) -> ProjectionAngles:
        num_slices = min(self.primary.num_images, self.secondary.num_images)
        return ProjectionAngles(np.deg2rad(np.linspace(0, 180, num_slices, endpoint=False)))

    @parameterized.expand([
        ("without_angles", False),
        ("with_matching_angles", True),
    ])
    def test_sum_stacks_correct_result(self, _name, use_angles):
        if use_angles:
            projection_angles = self._make_projection_angles()
            self.primary.set_projection_angles(projection_angles)
            self.secondary.set_projection_angles(projection_angles)

        primary_copy = self.primary.data.copy()
        secondary_copy = self.secondary.data.copy()
        expected = primary_copy + secondary_copy

        SumIntensitiesFilter.sum_stacks(self.primary, self.secondary)

        npt.assert_array_equal(self.primary.data, expected)
        npt.assert_array_equal(self.secondary.data, secondary_copy)  # Validate secondary stack is unchanged

    def test_prepare_angles_extracts_and_converts_radians_to_degrees(self):
        projection_angles = self._make_projection_angles()
        self.primary.set_projection_angles(projection_angles)
        self.secondary.set_projection_angles(projection_angles)

        angles = SumIntensitiesFilter._prepare_angles(self.primary, self.secondary)

        assert angles is not None
        primary_deg, secondary_deg = angles
        expected_deg = np.rad2deg(projection_angles.value)
        npt.assert_allclose(primary_deg, expected_deg, rtol=1e-5)
        npt.assert_allclose(secondary_deg, expected_deg, rtol=1e-5)

    def test_prepare_angles_returns_none_when_angles_missing(self):
        angles = SumIntensitiesFilter._prepare_angles(self.primary, self.secondary)
        self.assertIsNone(angles)

    @parameterized.expand([
        ("no_mismatch", 0.0, 0),
        ("within_threshold", 0.5, 3),
        ("exceeds_threshold", 2.0, 3),
    ])
    def test_check_angle_mismatch(self, _name, angle_offset, expected_mismatch_count):
        primary_angles_deg = np.rad2deg(self._make_projection_angles().value)
        secondary_angles_deg = primary_angles_deg + angle_offset

        mismatches = SumIntensitiesFilter._check_angle_mismatch(primary_angles_deg, secondary_angles_deg)

        self.assertEqual(len(mismatches), expected_mismatch_count)

    def test_check_shapes_match_same_shape(self):
        error = SumIntensitiesFilter._check_shapes_match(self.primary, self.secondary)
        self.assertIsNone(error)

    def test_check_shapes_match_different_shape(self):
        different_shape_stack = th.generate_images(shape=(5, 8, 10))
        error = SumIntensitiesFilter._check_shapes_match(self.primary, different_shape_stack)

        self.assertIsNotNone(error)
        self.assertIn(self.primary.name, error)
        self.assertIn(different_shape_stack.name, error)

    def test_get_notification_text_with_angle_mismatch(self):
        projection_angles = self._make_projection_angles()
        self.primary.set_projection_angles(projection_angles)
        secondary_angles = ProjectionAngles(projection_angles.value + np.deg2rad(2.0))
        self.secondary.set_projection_angles(secondary_angles)

        notification = SumIntensitiesFilter._get_notification_text(self.primary, self.secondary)

        self.assertIn("Warning", notification)
        self.assertIn("Append Stacks", notification)

    def test_get_notification_text_with_matching_angles_returns_none(self):
        projection_angles = self._make_projection_angles()
        self.primary.set_projection_angles(projection_angles)
        self.secondary.set_projection_angles(projection_angles)

        notification = SumIntensitiesFilter._get_notification_text(self.primary, self.secondary)

        self.assertIsNone(notification)

    def test_get_notification_text_no_angles(self):
        notification = SumIntensitiesFilter._get_notification_text(self.primary, self.secondary)

        self.assertIn("No projection angles", notification)

    def test_sum_stacks_preview_single_slice_primary(self):
        primary_preview = th.generate_images(shape=(1, *self.primary.data.shape[1:]))
        secondary_full = th.generate_images(shape=self.secondary.data.shape)
        primary_preview.data[:] = self.primary.data[:1]
        secondary_full.data[:] = self.secondary.data
        expected = self.primary.data[:1] + self.secondary.data[:1]

        SumIntensitiesFilter.sum_stacks(primary_preview, secondary_full)

        np.testing.assert_array_equal(primary_preview.data, expected)
        np.testing.assert_array_equal(secondary_full.data, self.secondary.data)  # Secondary unchanged
