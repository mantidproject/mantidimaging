# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import threading
import numpy as np

from typing import Any
from collections.abc import Callable

from pyqtgraph import PlotWidget, ImageView

from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.mvp_base import BaseDialogView
from .presenter import AsyncTaskDialogPresenter

from PyQt5.QtWidgets import QMainWindow, QPushButton
from PyQt5.QtCore import QTimer


class AsyncTaskDialogView(BaseDialogView):
    _presenter: AsyncTaskDialogPresenter | None

    def __init__(self, parent: QMainWindow):
        super().__init__(parent, "gui/ui/async_task_dialog.ui")
        # launch the dialog in center of screen
        self.move(QMainWindow().geometry().center() - self.rect().center())

        self._presenter = AsyncTaskDialogPresenter(self)

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(1000)

        self.show_timer = QTimer(self)
        self.progress_plot = PlotWidget()
        self.layout().addWidget(self.progress_plot)
        self.progress_plot.hide()
        self.progress_plot.setLogMode(y=True)
        self.progress_plot.setMinimumHeight(300)
        self.stop_recon_btn = QPushButton("Stop Reconstruction")
        self.layout().addWidget(self.stop_recon_btn)
        self.stop_recon_btn.hide()
        self.stop_recon_btn.clicked.connect(self.presenter.stop_reconstruction)
        self.hide()
        self.residual_image_view = ImageView()
        self.residual_image_view.setMinimumHeight(400)
        self.residual_image_view.setMinimumWidth(600)
        self.layout().addWidget(self.residual_image_view)
        self.residual_image_view.hide()
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
        print(f"AsyncTaskDialogView.set_progress() {threading.get_ident()}")
        # Set status message
        if message:
            self.infoText.setText(message)

        # Update progress bar
        self.progressBar.setValue(int(progress * 1000))

    def set_progress_plot(self, x, y):
        print(f"AsyncTaskDialogView.set_progress_plot() {threading.get_ident()}")
        self.progress_plot.show()
        self.progress_plot.plotItem.plot(x, y)
        self.stop_recon_btn.show()

    def set_progress_residual_plot(self, residual_image: np.ndarray):
        self.residual_image_view.show()
        max_level = np.percentile(residual_image, 99)
        self.residual_image_view.setImage(residual_image, levels=(0, max_level))
        self.residual_image_view.setLevels(0, residual_image.max())
        self.residual_image_view.ui.histogram.gradient.loadPreset("viridis")

    def show_delayed(self, timeout) -> None:
        self.show_timer.singleShot(timeout, self.show_from_timer)
        self.show_timer.start()

    def show_from_timer(self) -> None:
        # Might not run until after handle_completion
        if self._presenter is not None and self.presenter.task_is_running:
            self.show()


def start_async_task_view(
    parent: QMainWindow,
    task: Callable,
    on_complete: Callable,
    kwargs: dict | None = None,
    tracker: set[Any] | None = None,
    busy: bool | None = False,
):
    atd = AsyncTaskDialogView(parent)
    if not kwargs:
        kwargs = {"progress": Progress()}
    else:
        kwargs["progress"] = Progress()
    kwargs["progress"].add_progress_handler(atd.presenter)

    if busy:
        atd.progressBar.setMinimum(0)
        atd.progressBar.setMaximum(0)

    atd.presenter.set_task(task)
    atd.presenter.set_on_complete(on_complete)
    atd.presenter.set_parameters(**kwargs)
    if tracker is not None:
        atd.presenter.set_tracker(tracker)
    atd.presenter.do_start_processing()
