from __future__ import (absolute_import, division, print_function)

import unittest
import time

from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.dialogs.async_task import AsyncTaskDialogModel

mock = import_mock()


class AsyncTaskDialogModelTest(unittest.TestCase):

    def test_basic_happy_case(self):
        def f(a, b):
            time.sleep(0.1)
            return a + b

        done_func = mock.MagicMock()

        m = AsyncTaskDialogModel()
        m.task.task_function = f
        m.task.kwargs = {'a': 5, 'b': 4}
        m.on_complete_function = done_func
        self.assertFalse(m.task_is_running)

        m.do_execute_async()
        self.assertTrue(m.task_is_running)

        m.task.wait()
        self.assertFalse(m.task_is_running)
