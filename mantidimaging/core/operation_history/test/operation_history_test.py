import unittest

from mantidimaging.core.data import Images
from mantidimaging.core.operation_history import operations
from mantidimaging.core.operation_history.operations import (MODULE_NOT_FOUND, ImageOperation)


class OperationHistoryTest(unittest.TestCase):

    def test_finds_modules(self):
        in_ops = [ImageOperation("RebinFilter", [], {}), ImageOperation("MedianFilter", [], {})]
        ops = operations.ops_to_partials(in_ops)
        # expand the generator to see all functions
        ops = list(ops)
        self.assertEqual(len(ops), len(in_ops))

    def test_bad_module(self):
        fake_module_name = "NonExistingFilter12"
        in_ops = [ImageOperation(fake_module_name, [], {})]
        ops = operations.ops_to_partials(in_ops)
        with self.assertRaisesRegex(KeyError, MODULE_NOT_FOUND.format(fake_module_name)) as ctx:
            list(ops)
