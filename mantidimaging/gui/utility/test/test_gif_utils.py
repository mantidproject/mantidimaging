# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
import pytest
from parameterized import parameterized

from mantidimaging.gui.utility.gif_utils import (
    estimate_gif_size,
    calculate_optimal_frame_skip,
    _calculate_min_skip_for_angular_resolution,
    _calculate_max_skip_for_file_size,
    _find_optimal_divisor,
)


@pytest.mark.unit
class TestEstimateGifSize(unittest.TestCase):

    def test_basic_size_estimation_calculation(self):
        result = estimate_gif_size(26, 393, 229)
        self.assertAlmostEqual(result, 1.8, delta=0.2)

    @parameterized.expand([
        ("zero_frame_count", 0, 512, 512, 0.0),
        ("zero_width", 10, 512, 0, 0.0),
        ("zero_height", 10, 0, 512, 0.0),
    ])
    def test_zero_inputs(self, _, frames, height, width, expected):
        result = estimate_gif_size(frames, height, width)
        self.assertEqual(result, expected)


@pytest.mark.unit
class TestCalculateMinSkipForAngularResolution(unittest.TestCase):

    @parameterized.expand([
        ("360_angles_one_degree", 360, 1),
        ("180_angles_two_degrees", 180, 2),
        ("single_angle", 1, 360),
        ("fractional_result_ceiling", 100, 4),
    ])
    def test_angular_resolution_calculation(self, _, angle_count, expected_skip):
        """Test angular resolution skip calculation with various angle counts"""
        result = _calculate_min_skip_for_angular_resolution(angle_count)
        self.assertEqual(result, expected_skip)


@pytest.mark.unit
class TestCalculateMaxSkipForFileSize(unittest.TestCase):

    def test_very_large_image_high_skip(self):
        """Very large images should result in higher skip due to file size"""
        # Realistic dataset (IMAT00010675): 1143 projections, 393x229 cropped ROI
        result_realistic = _calculate_max_skip_for_file_size(projection_count=1143,
                                                             image_height=393,
                                                             image_width=229,
                                                             max_size_mb=5.0)
        # Compare with larger images requiring higher skip
        result_large = _calculate_max_skip_for_file_size(projection_count=1143,
                                                         image_height=2048,
                                                         image_width=2048,
                                                         max_size_mb=5.0)
        self.assertGreater(result_large, result_realistic)


@pytest.mark.unit
class TestFindOptimalDivisor(unittest.TestCase):

    @parameterized.expand([
        ("perfect_divisor_available", 1100, 50, 50, False),
        ("off_by_one_uses_plus_one", 100, 7, 7, False),
        ("off_by_one_uses_minus_one", 1200, 51, 50, True),
    ])
    def test_find_optimal_divisor(self, _, projection_count, target_skip, expected_result, check_divisible):
        result = _find_optimal_divisor(projection_count, target_skip)
        if check_divisible:
            self.assertEqual(projection_count % result, 0)
        else:
            self.assertEqual(result, expected_result)


@pytest.mark.unit
class TestCalculateOptimalFrameSkip(unittest.TestCase):

    def test_file_size_constraint_binding(self):
        """
        When file size is tight, should return higher skip
        Based on IMAT00010675: 1143 projections, 393x229 with tight vs loose size constraints
        """
        result_tight = calculate_optimal_frame_skip(
            projection_count=1143,
            image_height=393,
            image_width=229,
            angle_count=1143,
            max_size_mb=2.0  # Tight size constraint
        )
        result_loose = calculate_optimal_frame_skip(
            projection_count=1143,
            image_height=393,
            image_width=229,
            angle_count=1143,
            max_size_mb=50.0  # loose size constraint
        )
        self.assertGreater(result_tight, result_loose)

    def test_angular_resolution_constraint_binding(self):
        """When many angles, calculate_optimal_frame_skip should not skip too aggressively"""
        # Few angles, loose file size constraint
        result_few_angles = calculate_optimal_frame_skip(projection_count=100,
                                                         image_height=256,
                                                         image_width=256,
                                                         angle_count=10,
                                                         max_size_mb=50.0)
        # Many angles, loose file size constraint
        result_many_angles = calculate_optimal_frame_skip(projection_count=100,
                                                          image_height=256,
                                                          image_width=256,
                                                          angle_count=200,
                                                          max_size_mb=50.0)
        self.assertLess(result_many_angles, result_few_angles)

    def test_angle_count_none_uses_projection_count(self):
        """When angle_count is None, assume it equals projection_count"""
        result_explicit = calculate_optimal_frame_skip(projection_count=100,
                                                       image_height=256,
                                                       image_width=256,
                                                       angle_count=100)
        result_implicit = calculate_optimal_frame_skip(projection_count=100,
                                                       image_height=256,
                                                       image_width=256,
                                                       angle_count=None)
        self.assertEqual(result_explicit, result_implicit)

    def test_small_image_small_skip(self):
        """Small images should allow smaller skip values"""
        result_small = calculate_optimal_frame_skip(projection_count=1000,
                                                    image_height=128,
                                                    image_width=128,
                                                    max_size_mb=5.0)
        result_large = calculate_optimal_frame_skip(projection_count=1000,
                                                    image_height=2048,
                                                    image_width=2048,
                                                    max_size_mb=5.0)
        self.assertLess(result_small, result_large)


@pytest.mark.unit
class TestGifUtilsIntegration(unittest.TestCase):

    def test_size_estimation_with_optimal_skip(self):
        """Test that optimal skip produces reasonable size estimate"""
        # Based on IMAT00010675: 1143 projections, 393x229 cropped ROI
        projection_count = 1143
        image_height = 393
        image_width = 229

        optimal_skip = calculate_optimal_frame_skip(projection_count=projection_count,
                                                    image_height=image_height,
                                                    image_width=image_width,
                                                    max_size_mb=5.0)

        resulting_frames = projection_count // optimal_skip
        estimated_size = estimate_gif_size(resulting_frames, image_height, image_width)

        # Should be close to or under 5MB target
        self.assertLess(estimated_size, 6.0)  # Allow slight overshoot
