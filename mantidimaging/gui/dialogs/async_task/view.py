# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import Callable, Dict, Optional

from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.mvp_base import BaseDialogView
from .presenter import AsyncTaskDialogPresenter

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer


class AsyncTaskDialogView(BaseDialogView):
    def __init__(self, parent: QMainWindow, auto_close: bool = False):
        super().__init__(parent, 'gui/ui/async_task_dialog.ui')

        self.parent_view = parent
        self.presenter = AsyncTaskDialogPresenter(self)
        self.auto_close = auto_close

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(1000)

        self.show_timer = QTimer(self)
        self.hide()

    def handle_completion(self, successful: bool):
        """
        Updates the UI after the task has been completed.

        :param successful: If the task was successful
        """
        self.show_timer.stop()
        if successful:
            # Set info text to "Complete"
            self.infoText.setText("Complete")
        else:
            self.infoText.setText("Task failed.")

        # If auto close is enabled and the task was successful then hide the UI
        if self.auto_close:
            self.hide()

    def set_progress(self, progress: float, message: str):
        # Set status message
        if message:
            self.infoText.setText(message)

        # Update progress bar
        self.progressBar.setValue(int(progress * 1000))

    def show_delayed(self, timeout):
        self.show_timer.singleShot(timeout, self.show_from_timer)
        self.show_timer.start()

    def show_from_timer(self):
        if self.presenter.task_is_running:
            self.show()


def start_async_task_view(parent: QMainWindow, task: Callable, on_complete: Callable, kwargs: Optional[Dict] = None):
    atd = AsyncTaskDialogView(parent, auto_close=True)
    if not kwargs:
        kwargs = {'progress': Progress()}
    else:
        kwargs['progress'] = Progress()
    kwargs['progress'].add_progress_handler(atd.presenter)

    atd.presenter.set_task(task)
    atd.presenter.set_on_complete(on_complete)
    atd.presenter.set_parameters(**kwargs)
    atd.presenter.do_start_processing()
