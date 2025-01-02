# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from unittest.mock import patch

import psutil
from psutil import NoSuchProcess, AccessDenied
from parameterized import parameterized

from mantidimaging.core.parallel import manager as pm

CURRENT_PID = 1234
OLD_PID = CURRENT_PID - 1


def _lookup_process_mock(pid) -> None:
    if pid == OLD_PID:
        raise NoSuchProcess(pid)
    elif pid != CURRENT_PID:
        raise AccessDenied


class ParallelManagerTest(unittest.TestCase):
    MEM_NAME_FORMATS = [("Correct", f'MI_{CURRENT_PID}_123-456-789', True),
                        ("Prefix", f'Other_{CURRENT_PID}_123-456-789', False), ("PID", 'MI_test_123-456-789', False),
                        ("Length", 'MI_1234', False), ("Separator", 'MI-1234-123-456-789', False)]

    @parameterized.expand(MEM_NAME_FORMATS)
    def test_is_mi_shared_mem(self, _, mem_name, expected):
        self.assertEqual(expected, pm._is_mi_shared_mem(mem_name))

    def test_generate_mi_shared_mem_name_is_correct_format(self):
        generated_name = pm.generate_mi_shared_mem_name()
        self.assertTrue(pm._is_mi_shared_mem(generated_name))

    @parameterized.expand(MEM_NAME_FORMATS + [("Old_PID", f'MI_{OLD_PID}_123-456-789', False)])
    def test_is_mi_memory_from_current_process(self, _, mem_name, expected):
        with patch('mantidimaging.core.parallel.manager.CURRENT_PID', CURRENT_PID):
            self.assertEqual(expected, pm._is_mi_memory_from_current_process(mem_name))

    @patch('mantidimaging.core.parallel.manager._get_shared_mem_names_linux')
    def test_find_memory_from_previous_process_linux_no_mem_to_clear(self, _mock_get_shared_mem_names_linux):
        _mock_get_shared_mem_names_linux.return_value = []
        self.assertEqual([], pm.find_memory_from_previous_process_linux())

    @patch('mantidimaging.core.parallel.manager._get_shared_mem_names_linux')
    @patch('os.path.getmtime')
    @patch('mantidimaging.core.parallel.manager._lookup_process', new_callable=lambda: _lookup_process_mock)
    def test_find_memory_from_previous_process_linux_with_mem_to_clear(self, _mock_lookup_process, _mock_getmtime,
                                                                       _mock_get_shared_mem_names_linux):
        all_mem_files = [
            f'MI_{CURRENT_PID}_123', f'Other_{CURRENT_PID}_123', f'MI_{OLD_PID}_123', f'MI_{CURRENT_PID + 2}_123',
            f'MI_{OLD_PID}_124', 'MI_1234', 'MI_test_123-456-789', 'MI-1234-125'
        ]
        files_to_remove = [f'MI_{OLD_PID}_123', f'MI_{OLD_PID}_124']

        _mock_get_shared_mem_names_linux.return_value = all_mem_files
        _mock_getmtime.return_value = psutil.Process().create_time() - 3600

        self.assertEqual(files_to_remove, pm.find_memory_from_previous_process_linux())
