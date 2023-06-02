# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest.mock import Mock

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.ring_removal import RingRemovalFilter


class RingRemovalTest(unittest.TestCase):
    """
    Test ring removal filter.

    Tests return value and in-place modified data.
    """

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        images = th.generate_images()
        mocks = [Mock()] + [Mock(value=lambda: 0) for _ in range(7)]
        RingRemovalFilter.execute_wrapper(*mocks)(images)


if __name__ == '__main__':
    unittest.main()
