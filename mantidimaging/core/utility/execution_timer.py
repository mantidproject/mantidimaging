# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import time


class ExecutionTimer(object):
    """
    Context handler used to time the execution of code in it's context.
    """

    def __init__(self, msg='Elapsed time'):
        self.msg = msg

        self.time_start = None
        self.time_end = None

    def __str__(self):
        prefix = f'{self.msg}: ' if self.msg else ''
        sec = self.total_seconds
        return f'{prefix}{sec if sec else "unknown"} seconds'

    def __enter__(self):
        self.time_start = time.time()
        self.time_end = None

    def __exit__(self, *args):
        self.time_end = time.time()

    @property
    def total_seconds(self):
        """
        Gets the total number of seconds the timer was running for, returns
        None if the timer has not been run or is still running.
        """
        return self.time_end - self.time_start if \
            self.time_start and self.time_end else None
