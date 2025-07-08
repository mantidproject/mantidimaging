# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from logging import getLogger
from collections.abc import Callable

from PyQt5.QtCore import QThread

from mantidimaging.core.utility.func_call import call_with_known_parameters
from mantidimaging.core.utility.progress_reporting.progress import TaskCancelled


class TaskWorkerThread(QThread):
    """
    Thread for running tasks asynchronously to the GUI.

    Intended for internal use within this module only.

    Usage:
        t = TaskWorkerThread(parent)
        t.task_function = ...
        t.finished.connect(...)
        t.start()

    On completion inspect:
        t.result
        t.error
    """

    task_function: Callable | None
    error: Exception | None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.task_function = None
        self.kwargs = {}
        self.result = None
        self.error = None

    def run(self) -> None:
        log = getLogger(__name__)

        try:
            if self.task_function is None:
                raise ValueError("No task function provided")

            self.result = call_with_known_parameters(self.task_function, **self.kwargs)

        except TaskCancelled as e:
            log.info("Task was cancelled by the user.")
            self.result = None
            self.error = e
            return

        except Exception as e:
            log.exception(f"Failed to execute task: {e}")
            self.result = None
            self.error = e
            return

    def was_successful(self) -> bool:
        """
        Inspects the result and error values of the async task.

        For a task to be "successful" the result must have a value and the
        error must be None.

        :return: True if task finished successfully
        """
        return self.result is not None and self.error is None
