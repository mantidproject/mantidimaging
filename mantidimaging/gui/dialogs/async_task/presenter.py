# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import traceback
from logging import getLogger
from enum import Enum

from collections.abc import Callable

from PyQt5.QtCore import QObject, pyqtSignal

from mantidimaging.core.utility.progress_reporting import ProgressHandler
from .model import AsyncTaskDialogModel


class Notification(Enum):
    START = 1


class AsyncTaskDialogPresenter(QObject, ProgressHandler):
    progress_updated = pyqtSignal(float, str)

    def __init__(self, view):
        super().__init__()

        self.view = view
        self.progress_updated.connect(self.view.set_progress)

        self.model = AsyncTaskDialogModel()
        self.model.task_done.connect(self.view.handle_completion)

    def notify(self, signal) -> None:
        try:
            if signal == Notification.START:
                self.do_start_processing()

        except Exception as e:
            self.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def set_task(self, f: Callable) -> None:
        self.model.task.task_function = f

    def set_parameters(self, **kwargs) -> None:
        self.model.task.kwargs = kwargs

    def set_on_complete(self, f: Callable) -> None:
        self.model.on_complete_function = f

    def set_tracker(self, tracker: set) -> None:
        self.model.set_tracker(tracker)

    def do_start_processing(self) -> None:
        """
        Starts async task execution and shows GUI.
        """
        self.model.do_execute_async()
        self.view.show_delayed(1000)

    @property
    def task_is_running(self) -> None:
        return self.model.task_is_running

    def progress_update(self) -> None:
        msg = self.progress.last_status_message()
        self.progress_updated.emit(self.progress.completion(), msg if msg is not None else '')

    def show_stop_button(self, show: bool = False) -> None:
        self.view.show_cancel_button(show)

    def stop_progress(self):
        self.progress.cancel("Cancelled by user")
