# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
Context managers for logging execution time or profile of code.

These are not used in the code, but are here as developer tools. They can be used by wrapping the code of interest::

    with ExecutionProfiler(msg="a_slow_function()"):
        a_slow_function()

They will display to the performance log if a logger object is not given. See the developer docs to enable performance
logging.
"""

from __future__ import annotations

import cProfile
import time
from io import StringIO
from logging import getLogger, Logger
from pstats import Stats

perf_logger = getLogger("perf." + __name__)


class ExecutionTimer:
    """
    Context manager used to time the execution of code in its context.
    """

    def __init__(self, msg: str = 'Elapsed time', logger: Logger = perf_logger):
        self.msg = msg
        self.logger = logger

        self.time_start: float | None = None
        self.time_end: float | None = None

    def __str__(self):
        prefix = f'{self.msg}: ' if self.msg else ''
        sec = self.total_seconds
        return f'{prefix}{sec if sec else "unknown"} seconds'

    def __enter__(self):
        self.time_start = time.monotonic()
        self.time_end = None

    def __exit__(self, *args):
        self.time_end = time.monotonic()
        self.logger.info(str(self))

    @property
    def total_seconds(self):
        """
        Gets the total number of seconds the timer was running for, returns
        None if the timer has not been run or is still running.
        """
        return self.time_end - self.time_start if \
            self.time_start and self.time_end else None


class ExecutionProfiler:
    """
    Context manager used to profile the execution of code in its context.


    """

    def __init__(self,
                 msg: str = 'Elapsed time',
                 logger: Logger = perf_logger,
                 max_lines: int = 20,
                 sort_by: str = "cumtime"):
        self.msg = msg
        self.logger = logger
        self.max_lines = max_lines
        self.sort_by = sort_by

        self.pr = cProfile.Profile()

    def __str__(self):
        out = StringIO()
        out.write(f'{self.msg}: \n' if self.msg else '')

        ps = Stats(self.pr, stream=out).sort_stats(self.sort_by)
        ps.print_stats()
        return out.getvalue()

    def __enter__(self):
        self.pr.enable()

    def __exit__(self, *args):
        self.pr.disable()
        if perf_logger.isEnabledFor(1):
            for line in str(self).split("\n")[:self.max_lines]:
                self.logger.info(line)
