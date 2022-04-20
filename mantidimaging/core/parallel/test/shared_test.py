# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock
from unittest.mock import patch

from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.parallel.utility import SharedArrayProxy


def _populate_shared_list(num_arrays, has_shared_mem):
    array_list = []
    for n in range(num_arrays):
        mock_array = mock.Mock()
        mock_array.has_shared_memory = has_shared_mem
        mock_array.array_proxy = SharedArrayProxy(None, (2, 2), 'float32') if has_shared_mem else mock.Mock()
        array_list.append(mock_array)
    return array_list


class SharedTest(unittest.TestCase):
    @patch('mantidimaging.core.parallel.shared.shared_list', _populate_shared_list(5, True))
    def test_check_shared_mem_and_get_data_all_shared(self):
        all_in_shared_memory, data = ps._check_shared_mem_and_get_data()
        self.assertTrue(all_in_shared_memory)
        self.assertTrue(len(data) == 5)
        self.assertTrue(isinstance(data[0], SharedArrayProxy))

    @patch('mantidimaging.core.parallel.shared.shared_list', _populate_shared_list(5, False))
    def test_check_shared_mem_and_get_data_none_shared(self):
        all_in_shared_memory, data = ps._check_shared_mem_and_get_data()
        self.assertFalse(all_in_shared_memory)
        self.assertTrue(len(data) == 5)
        self.assertTrue(isinstance(data[0], mock.Mock))

    @patch('mantidimaging.core.parallel.shared.shared_list',
           _populate_shared_list(3, True) + _populate_shared_list(2, False))
    def test_check_shared_mem_and_get_data_some_shared(self):
        all_in_shared_memory, data = ps._check_shared_mem_and_get_data()
        self.assertFalse(all_in_shared_memory)
        self.assertTrue(len(data) == 5)
        self.assertTrue(isinstance(data[0], mock.Mock))
