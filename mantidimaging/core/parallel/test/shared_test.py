# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from unittest import mock

from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.parallel.utility import SharedArrayProxy


class SharedTest(unittest.TestCase):

    def test_check_shared_mem_and_get_data_all_shared(self):
        arrays = self._create_array_list(5, True)
        all_in_shared_memory, data = ps._check_shared_mem_and_get_data(arrays)
        self.assertTrue(all_in_shared_memory)
        self.assertTrue(len(data) == 5)
        self.assertTrue(isinstance(data[0], SharedArrayProxy))

    def test_check_shared_mem_and_get_data_none_shared(self):
        arrays = self._create_array_list(5, False)
        all_in_shared_memory, data = ps._check_shared_mem_and_get_data(arrays)
        self.assertFalse(all_in_shared_memory)
        self.assertTrue(len(data) == 5)
        self.assertTrue(isinstance(data[0], mock.Mock))

    def test_check_shared_mem_and_get_data_some_shared(self):
        arrays = self._create_array_list(3, True) + self._create_array_list(2, False)
        all_in_shared_memory, data = ps._check_shared_mem_and_get_data(arrays)
        self.assertFalse(all_in_shared_memory)
        self.assertTrue(len(data) == 5)
        self.assertTrue(isinstance(data[0], mock.Mock))

    def _create_array_list(self, num_arrays, has_shared_mem):
        array_list = []
        for _ in range(num_arrays):
            mock_array = mock.Mock()
            mock_array.has_shared_memory = has_shared_mem
            mock_array.array_proxy = SharedArrayProxy(None, (2, 2), 'float32') if has_shared_mem else mock.Mock()
            array_list.append(mock_array)
        return array_list
