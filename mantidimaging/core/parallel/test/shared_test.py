# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock
from unittest.mock import patch

from mantidimaging.core.parallel import shared as ps


def _populate_shared_list(num_arrays, has_shared_mem):
    array_list = []
    for n in range(num_arrays):
        mock_array = mock.Mock()
        mock_array.has_shared_memory = has_shared_mem
        mock_array.details = mock.Mock()
        array_list.append(mock_array)
    return array_list


class SharedTest(unittest.TestCase):
    @patch('mantidimaging.core.parallel.shared.shared_list', _populate_shared_list(5, True))
    def test_check_shared_mem_details_all_shared(self):
        all_in_shared_memory, details_list = ps._check_shared_mem_details()
        self.assertTrue(all_in_shared_memory)
        self.assertTrue(len(details_list) == 5)

    @patch('mantidimaging.core.parallel.shared.shared_list', _populate_shared_list(5, False))
    def test_check_shared_mem_details_none_shared(self):
        all_in_shared_memory, details_list = ps._check_shared_mem_details()
        self.assertFalse(all_in_shared_memory)
        self.assertTrue(len(details_list) == 0)

    @patch('mantidimaging.core.parallel.shared.shared_list',
           _populate_shared_list(3, True) + _populate_shared_list(2, False))
    def test_check_shared_mem_details_some_shared(self):
        all_in_shared_memory, details_list = ps._check_shared_mem_details()
        self.assertFalse(all_in_shared_memory)
        self.assertTrue(len(details_list) == 0)

    @patch('mantidimaging.core.parallel.utility.lookup_shared_arrays')
    def test_get_array_list_with_array_details(self, mock_lookup_shared_arrays):
        mock_details = mock.Mock()
        mock_list = mock.Mock()
        mock_lookup_shared_arrays.return_value = mock_list

        array_list = ps._get_array_list([mock_details])
        mock_lookup_shared_arrays.assert_called_once()
        self.assertIs(array_list, mock_list)

    @patch('mantidimaging.core.parallel.shared.shared_list', [mock.Mock])
    @patch('mantidimaging.core.parallel.utility.lookup_shared_arrays')
    def test_get_array_list_without_array_details(self, mock_lookup_shared_arrays):
        array_list = ps._get_array_list([])
        mock_lookup_shared_arrays.assert_not_called()
        self.assertIs(array_list, ps.shared_list)
