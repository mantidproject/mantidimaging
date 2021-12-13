# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
import time

from mantidimaging.core.utility import ExecutionTimer


class ExecutionTimerTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_execute(self):
        t = ExecutionTimer()
        self.assertEqual(t.total_seconds, None)
        self.assertEqual(str(t), 'Elapsed time: unknown seconds')

        with t:
            self.assertEqual(t.total_seconds, None)
            self.assertEqual(str(t), 'Elapsed time: unknown seconds')

            time.sleep(0.1)

        self.assertAlmostEqual(t.total_seconds, 0.1, delta=0.05)

    def test_custom_message(self):
        t = ExecutionTimer(msg='Task')
        self.assertEqual(str(t), 'Task: unknown seconds')

    def test_custom_message_empty(self):
        t = ExecutionTimer(msg='')
        self.assertEqual(str(t), 'unknown seconds')

    def test_custom_message_none(self):
        t = ExecutionTimer(msg=None)
        self.assertEqual(str(t), 'unknown seconds')
