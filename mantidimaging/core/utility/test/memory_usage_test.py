# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest.mock import patch, Mock

from mantidimaging.core.utility.memory_usage import (MEMORY_CAP_PERCENTAGE, system_free_memory, get_memory_usage_linux,
                                                     get_memory_usage_linux_str)


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

        memory_kb, memory_mb = get_memory_usage_linux(kb=True, mb=True)
        self.assertEqual(memory_kb, 4 * 1024 * 1024)
        self.assertEqual(memory_mb, 4 * 1024)

    @patch('mantidimaging.core.utility.memory_usage.get_memory_usage_linux')
    def test_get_memory_usage_linux_str(self, mock_get_memory_usage_linux):
        mock_get_memory_usage_linux.return_value = (4096, 4)  # 4096 KB and 4 MB

        memory_str = get_memory_usage_linux_str()
        self.assertIn("4096 KB, 4 MB", memory_str)

        # Check memory change part
        memory_str = get_memory_usage_linux_str()
        self.assertIn("Memory change: 0.0 MB", memory_str)


if __name__ == '__main__':
    unittest.main()
