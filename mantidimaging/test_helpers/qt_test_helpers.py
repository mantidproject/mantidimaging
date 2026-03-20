# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections.abc import Callable

from PyQt5.QtTest import QTest


def wait_until(test_func: Callable[[], bool],
               delay=0.1,
               max_retry=100,
               message: str = "wait_until reached max retries"):
    """
    Repeat test_func every delay seconds until it becomes true. Raises RuntimeError if max_retry is reached.
    """
    for _ in range(max_retry):
        if test_func():
            return True
        QTest.qWait(int(delay * 1000))
    raise RuntimeError(message)
