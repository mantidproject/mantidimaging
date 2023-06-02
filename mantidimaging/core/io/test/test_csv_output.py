# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import io
import unittest

import numpy as np

from mantidimaging.core.io.csv_output import CSVOutput


class CSVOutputTest(unittest.TestCase):

    def setUp(self) -> None:
        self.stream = io.StringIO()
        self.csv_output = CSVOutput()

    def test_add_column(self):
        col_name = "new_col"
        values = np.arange(10)

        self.csv_output.add_column(col_name, values)

        self.assertIn(col_name, self.csv_output.columns)
        np.testing.assert_array_equal(self.csv_output.columns[col_name].flatten(), values.flatten())

    def test_column_order(self):
        col_names = "red orange yellow green blue indigo violet".split()
        for col_name in col_names:
            self.csv_output.add_column(col_name, np.arange(10))

        self.assertEqual(col_names, list(self.csv_output.columns.keys()))

    def test_write_single(self):
        col_name = "new_col"
        values = np.arange(5, dtype=np.float32)
        expected_out = "# new_col\n0.0\n1.0\n2.0\n3.0\n4.0\n"
        self.csv_output.add_column(col_name, values)

        self.csv_output.write(self.stream)
        self.assertEqual(self.stream.getvalue(), expected_out)

    def test_write_2_cols(self):
        expected_out = "# col_1,col_2\n0.0,5.0\n1.0,6.0\n2.0,7.0\n3.0,8.0\n4.0,9.0\n"
        self.csv_output.add_column("col_1", np.arange(5, dtype=np.float32))
        self.csv_output.add_column("col_2", np.arange(5, 10, dtype=np.float32))

        self.csv_output.write(self.stream)
        self.assertEqual(self.stream.getvalue(), expected_out)

    def test_add_column_wrong_size(self):
        self.csv_output.add_column("col_1", np.arange(5, dtype=np.float32))

        with self.assertRaises(ValueError):
            self.csv_output.add_column("col_2", np.arange(6, dtype=np.float32))
