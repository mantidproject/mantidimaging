# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Any
from collections.abc import Callable

from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.mvp_base import BaseDialogView
from .presenter import AsyncTaskDialogPresenter

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer


class AsyncTaskDialogView(BaseDialogView):
    _presenter: AsyncTaskDialogPresenter | None

    def __init__(self, parent: QMainWindow):
        super().__init__(parent, 'gui/ui/async_task_dialog.ui')

        self._presenter = AsyncTaskDialogPresenter(self)

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(1000)

        self.show_timer = QTimer(self)
        self.cancelButton.clicked.connect(self.presenter.stop_progress)
        self.cancelButton.hide()
        self.hide()

    @property
    def presenter(self) -> AsyncTaskDialogPresenter:
        if self._presenter is None:
            raise RuntimeError("Presenter accessed after handle_completion")
        return self._presenter

    def handle_completion(self, successful: bool) -> None:
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

        self.close()
        self.setParent(None)

        self.presenter.progress = None
        self.presenter.model = None
        self._presenter = None

    def set_progress(self, progress: float, message: str):
        # Set status message
        if message:
            self.infoText.setText(message)

        # Update progress bar
        self.progressBar.setValue(int(progress * 1000))

    def show_delayed(self, timeout) -> None:
        self.show_timer.singleShot(timeout, self.show_from_timer)
        self.show_timer.start()

    def show_from_timer(self) -> None:
        # Might not run until after handle_completion
        if self._presenter is not None and self.presenter.task_is_running:
            self.show()

    def show_cancel_button(self, cancelable: bool) -> None:
        if cancelable:
            self.cancelButton.show()
        else:
            self.cancelButton.hide()


def start_async_task_view(parent: QMainWindow,
                          task: Callable,
                          on_complete: Callable,
                          kwargs: dict | None = None,
                          tracker: set[Any] | None = None,
                          busy: bool | None = False):
    atd = AsyncTaskDialogView(parent)
    if not kwargs:
        kwargs = {'progress': Progress()}
    else:
        kwargs['progress'] = Progress()
    kwargs['progress'].add_progress_handler(atd.presenter)

    if busy:
        atd.progressBar.setMinimum(0)
        atd.progressBar.setMaximum(0)

    atd.presenter.set_task(task)
    atd.presenter.set_on_complete(on_complete)
    atd.presenter.set_parameters(**kwargs)
    if tracker is not None:
        atd.presenter.set_tracker(tracker)
    atd.presenter.do_start_processing()
