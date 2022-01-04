# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from logging import getLogger

from PyQt5.QtCore import QThread

from mantidimaging.core.utility.func_call import call_with_known_parameters


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
    def __init__(self, parent=None):
        super().__init__(parent)

        self.task_function = None

        self.kwargs = {}

        self.result = None
        self.error = None

    def run(self):
        log = getLogger(__name__)

        try:
            if self.task_function is None:
                raise ValueError("No task function provided")

            self.result = call_with_known_parameters(self.task_function, **self.kwargs)

        except Exception as e:
            log.exception("Failed to execute task")
            self.result = None
            self.error = e

    def was_successful(self):
        """
        Inspects the result and error values of the async task.

        For a task to be "successful" the result must have a value and the
        error must be None.

        :return: True if task finished successfully
        """
        return self.result is not None and self.error is None
