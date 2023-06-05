# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from logging import getLogger
from typing import Callable, Optional, Set

from PyQt5.QtCore import QObject, pyqtSignal

from .task import TaskWorkerThread


class AsyncTaskDialogModel(QObject):

    # Signal emitted when task processing has terminated
    task_done = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()

        self.task = TaskWorkerThread()
        self.task.finished.connect(self._on_task_exit)

        self.on_complete_function: Optional[Callable] = None
        self.tracker: Optional[Set] = None

    def set_tracker(self, tracker: Set):
        self.tracker = tracker
        self.tracker.add(self)

    def do_execute_async(self) -> None:
        """
        Start asynchronous execution.
        """
        self.task.start()

    @property
    def task_is_running(self) -> bool:
        return self.task.isRunning()

    def _cleanup(self) -> None:
        if self.tracker is not None:
            self.tracker.remove(self)
        self.on_complete_function = None
        self.task.task_function = None

    def _on_task_exit(self) -> None:
        """
        Handler for task thread completion.

        Forwards task_done signal and calls post processing function (if
        provided).
        """
        log = getLogger(__name__)

        # Emit on complete function
        self.task_done.emit(self.task.was_successful())

        # Call post process function
        if self.on_complete_function is not None:
            try:
                self.on_complete_function(self.task)
            except Exception:
                log.exception("Failed to run task completion callback")
                raise
            finally:
                self._cleanup()
        else:
            self._cleanup()
