import unittest
import time

from mantidimaging.core.utility import ExecutionTimer


class ExecutionTimerTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ExecutionTimerTest, self).__init__(*args, **kwargs)

    def test_execute(self):
        t = ExecutionTimer()
        self.assertEquals(t.total_seconds, None)
        self.assertEquals(str(t), 'Elapsed time: unknown seconds')

        with t:
            self.assertEquals(t.total_seconds, None)
            self.assertEquals(str(t), 'Elapsed time: unknown seconds')

            time.sleep(0.1)

        self.assertAlmostEqual(t.total_seconds, 0.1, delta=0.05)

    def test_custom_message(self):
        t = ExecutionTimer(msg='Task')
        self.assertEquals(str(t), 'Task: unknown seconds')

    def test_custom_message_empty(self):
        t = ExecutionTimer(msg='')
        self.assertEquals(str(t), 'unknown seconds')

    def test_custom_message_none(self):
        t = ExecutionTimer(msg=None)
        self.assertEquals(str(t), 'unknown seconds')
