# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

from mantidimaging.core.operation_history import operations
from mantidimaging.core.operation_history.operations import (MODULE_NOT_FOUND, ImageOperation)


class OperationHistoryTest(unittest.TestCase):

    def test_finds_modules(self):
        in_ops = [ImageOperation("RebinFilter", {}, "Rebin"), ImageOperation("MedianFilter", {}, "Median")]
        ops = operations.ops_to_partials(in_ops)
        # expand the generator to see all functions
        ops = list(ops)
        self.assertEqual(len(ops), len(in_ops))

    def test_bad_module(self):
        fake_module_name = "NonExistingFilter12"
        in_ops = [ImageOperation(fake_module_name, {}, "unknown")]
        ops = operations.ops_to_partials(in_ops)
        with self.assertRaisesRegex(KeyError, MODULE_NOT_FOUND.format(fake_module_name)):
            list(ops)
