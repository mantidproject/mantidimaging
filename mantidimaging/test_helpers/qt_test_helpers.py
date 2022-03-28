# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import Callable

from PyQt5.QtTest import QTest


def wait_until(test_func: Callable[[], bool], delay=0.1, max_retry=100):
    """
    Repeat test_func every delay seconds until is becomes true. Or if max_retry is reached return false.
    """
    for _ in range(max_retry):
        if test_func():
            return True
        QTest.qWait(int(delay * 1000))
    raise RuntimeError("wait_until reach max retries")
