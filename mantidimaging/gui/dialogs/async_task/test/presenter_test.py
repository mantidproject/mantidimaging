# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import time
import unittest

from unittest import mock

from mantidimaging.gui.dialogs.async_task import (AsyncTaskDialogPresenter, AsyncTaskDialogView)
from mantidimaging.gui.dialogs.async_task.presenter import Notification


class AsyncTaskDialogPresenterTest(unittest.TestCase):

    def test_basic_happy_case(self):

        def f(a, b):
            time.sleep(0.1)
            return a + b

        v = mock.create_autospec(AsyncTaskDialogView, instance=True)

        p = AsyncTaskDialogPresenter(v)
        p.set_task(f)
        p.set_parameters(a=3, b=4)
        self.assertFalse(p.task_is_running)

        p.notify(Notification.START)
        v.show_delayed.assert_called_once()
        self.assertTrue(p.task_is_running)

        p.model.task.wait()
        self.assertFalse(p.task_is_running)

        self.assertEqual(p.model.task.result, 7)
        self.assertIsNone(p.model.task.error)

    def test_basic_error_case(self):

        def f(a, b):
            time.sleep(0.1)
            return a / b

        v = mock.create_autospec(AsyncTaskDialogView, instance=True)

        p = AsyncTaskDialogPresenter(v)
        p.set_task(f)
        p.set_parameters(a=3, b=0)
        self.assertFalse(p.task_is_running)

        p.notify(Notification.START)
        v.show_delayed.assert_called_once()
        self.assertTrue(p.task_is_running)

        p.model.task.wait()
        self.assertFalse(p.task_is_running)

        self.assertIsNone(p.model.task.result)
        self.assertIsInstance(p.model.task.error, ZeroDivisionError)
