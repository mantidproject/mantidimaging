# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock

import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.gui.dialogs.op_history_copy import OpHistoryCopyDialogModel


class OpHistoryCopyDialogModelTest(unittest.TestCase):

    def setUp(self):
        self.images = ImageStack(data=np.ndarray(shape=(128, 10, 128), dtype=np.float32))
        self.images.data[:] = 100
        self.model = OpHistoryCopyDialogModel(self.images)

    @patch('mantidimaging.gui.dialogs.op_history_copy.model.ops_to_partials')
    def test_final_function_result_returned(self, mock_partial_conversions):
        expected = self.images
        call_mock = MagicMock()

        def fake_filter(_):
            call_mock()
            return 123

        mock_partial_conversions.return_value = [
            fake_filter,
        ]
        # Value passed to apply_ops is only used in ops_to_partial, which is mocked for
        # this test, so the value of the parameter shouldn't matter.
        result = self.model.apply_ops([1], copy=False)
        call_mock.assert_called_once()
        self.assertIs(expected, result)
        self.assertEqual(expected, result)
        np.testing.assert_equal(expected.data, result.data)

        call_mock.reset_mock()

        result = self.model.apply_ops([1], copy=True)
        call_mock.assert_called_once()
        self.assertIsNot(expected, result)
        self.assertEqual(expected, result)
        np.testing.assert_equal(expected.data, result.data)
