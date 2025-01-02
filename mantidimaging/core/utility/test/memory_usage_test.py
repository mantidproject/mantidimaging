# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest.mock import patch, Mock

from mantidimaging.core.utility.memory_usage import (MEMORY_CAP_PERCENTAGE, system_free_memory, get_memory_usage_linux)


class TestMemoryUtils(unittest.TestCase):

    @patch('psutil.virtual_memory')
    def test_system_free_memory(self, mock_virtual_memory):
        mock_meminfo = Mock()
        mock_meminfo.available = 8 * 1024 * 1024 * 1024  # 8 GB
        mock_meminfo.total = 16 * 1024 * 1024 * 1024  # 16 GB
        mock_virtual_memory.return_value = mock_meminfo

        free_mem = system_free_memory()
        expected_free_mem = 8 * 1024 * 1024 * 1024 - 16 * 1024 * 1024 * 1024 * MEMORY_CAP_PERCENTAGE

        self.assertAlmostEqual(free_mem._bytes, expected_free_mem)
        self.assertAlmostEqual(free_mem.kb(), expected_free_mem / 1024)
        self.assertAlmostEqual(free_mem.mb(), expected_free_mem / 1024 / 1024)

    @patch('psutil.virtual_memory')
    def test_get_memory_usage_linux(self, mock_virtual_memory):
        mock_meminfo = Mock()
        mock_meminfo.used = 4 * 1024 * 1024 * 1024  # 4 GB
        mock_virtual_memory.return_value = mock_meminfo

        memory_in_bytes = get_memory_usage_linux()
        self.assertEqual(memory_in_bytes, 4 * 1024 * 1024 * 1024)


if __name__ == '__main__':
    unittest.main()
