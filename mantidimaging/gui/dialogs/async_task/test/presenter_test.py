import time
import unittest

import mock

from mantidimaging.gui.dialogs.async_task import (AsyncTaskDialogPresenter, AsyncTaskDialogView)
from mantidimaging.gui.dialogs.async_task.presenter import Notification


class AsyncTaskDialogPresenterTest(unittest.TestCase):
    def _long_task(self):
        for ii in range(0, 10):
            time.sleep(1)
        # Shouldn't get here.
        self.assertTrue(False)

    def setUp(self):
        self.v = mock.create_autospec(AsyncTaskDialogView)
        self.p = AsyncTaskDialogPresenter(self.v)

    def test_basic_happy_case(self):
        def f(a, b):
            time.sleep(0.1)
            return a + b

        self.p.set_task(f)
        self.p.set_parameters([5], {'b': 4})
        self.assertFalse(self.p.task_is_running)

        self.p.notify(Notification.START)
        self.v.show.assert_called_once()
        self.assertTrue(self.p.task_is_running)

        self.p.model.task.wait()
        self.assertFalse(self.p.task_is_running)

    def test_async_task_cancelled(self):
        # Setup
        self.p.set_task(self._long_task)
        self.v.ask_user_if_they_are_sure_destructive.return_value = True
        self.assertFalse(self.p.task_is_running)

        # Start task
        self.p.notify(Notification.START)
        self.v.show.assert_called_once()
        self.assertTrue(self.p.task_is_running)

        # Cancel running task
        self.p.notify(Notification.CANCEL)
        self.assertFalse(self.p.task_is_running)
        self.v.ask_user_if_they_are_sure_destructive.assert_called_once()

    def test_async_task_doesnt_cancel(self):
        # Setup
        self.p.set_task(self._long_task)
        self.v.ask_user_if_they_are_sure_destructive.return_value = False
        self.assertFalse(self.p.task_is_running)

        # Start task
        self.p.notify(Notification.START)
        self.v.show.assert_called_once()
        self.assertTrue(self.p.task_is_running)

        # Cancel running task
        self.p.notify(Notification.CANCEL)
        self.assertTrue(self.p.task_is_running)
        self.v.ask_user_if_they_are_sure_destructive.assert_called_once()

        # Cleanup
        self.p.model.do_cancel_task()
