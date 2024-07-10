import unittest
from unittest.mock import patch, Mock

from mantidimaging.core.utility.memory_usage import (MEMORY_CAP_PERCENTAGE, system_free_memory, get_memory_usage_linux,
                                                     get_memory_usage_linux_str, debug_log_memory_usage_linux)


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

    @patch('resource.getrusage')
    @patch('logging.getLogger')
    def test_debug_log_memory_usage_linux(self, mock_getLogger, mock_getrusage):
        mock_log = Mock()
        mock_getLogger.return_value = mock_log
        mock_getrusage.return_value = Mock(ru_maxrss=500000)

        debug_log_memory_usage_linux("Test message")

        mock_log.info.assert_any_call("Memory usage 500000 KB, 488.28125 MB")
        mock_log.info.assert_any_call("Test message")

    @patch('resource.getrusage', side_effect=ImportError)
    @patch('logging.getLogger')
    def test_debug_log_memory_usage_linux_import_error(self, mock_getLogger, mock_getrusage):
        mock_log = Mock()
        mock_getLogger.return_value = mock_log

        debug_log_memory_usage_linux("Test message")

        mock_log.warning.assert_called_once_with('Resource monitoring is not available on Windows')


if __name__ == '__main__':
    unittest.main()
