# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import threading
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
    progress_plot_updated = pyqtSignal(list, list)

    def __init__(self, view):
        super().__init__()

        self.view = view
        self.progress_updated.connect(self.view.set_progress)
        self.progress_plot_updated.connect(self.view.set_progress_plot)

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
        print(f"AsyncTaskDialogPresenter.progress_update() {threading.get_ident()}")
        msg = self.progress.last_status_message()
        progress_info = self.progress.progress_history
        extra_info = progress_info[-1].extra_info
        self.progress_updated.emit(self.progress.completion(), msg if msg is not None else '')

        if extra_info:
            print(f"progress_update() {extra_info=}")
            x = extra_info['iterations']
            y = [a[0] for a in extra_info['losses']]
            self.progress_plot_updated.emit(x, y)

    def stop_reconstruction(self):
        print(f"Stopping Reconstruction() {threading.get_ident()}")
        self.progress.cancel("Stopped")
