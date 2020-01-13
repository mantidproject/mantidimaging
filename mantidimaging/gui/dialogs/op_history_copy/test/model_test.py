import unittest
from unittest.mock import patch, MagicMock

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.gui.dialogs.op_history_copy import OpHistoryCopyDialogModel


class OpHistoryCopyDialogModelTest(unittest.TestCase):
    def setUp(self):
        self.data = Images(sample=np.ndarray(shape=(128, 10, 128), dtype=np.float32))
        self.model = OpHistoryCopyDialogModel(self.data)

    @patch('mantidimaging.gui.dialogs.op_history_copy.model.ops_to_partials')
    def test_final_function_result_returned(self, mock_partial_conversions):
        expected = Images(sample=321)
        call_mock = MagicMock()

        def fake_filter(_):
            call_mock()
            return 123

        mock_partial_conversions.return_value = [
            fake_filter,
            lambda image: "123",
            lambda image: expected,
        ]
        # Value passed to apply_ops is only used in ops_to_partial, which is mocked for
        # this test, so the value of the parameter shouldn't matter.
        result = self.model.apply_ops(None)
        call_mock.assert_called_once()
        self.assertEqual(expected, result)
