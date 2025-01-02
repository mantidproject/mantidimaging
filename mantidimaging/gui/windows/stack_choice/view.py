# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QMainWindow, QMessageBox, QPushButton, QSizePolicy
from pyqtgraph import ViewBox

from mantidimaging.core.data.imagestack import ImageStack
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.mi_image_view.view import MIImageView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.stack_choice.compare_presenter import StackComparePresenter  # pragma: no cover
    from mantidimaging.gui.windows.stack_choice.presenter import StackChoicePresenter  # pragma: no cover


class Notification(Enum):
    CHOOSE_ORIGINAL = auto()
    CHOOSE_NEW_DATA = auto()
    TOGGLE_LOCK_HISTOGRAMS = auto()


class StackChoiceView(BaseMainWindowView):
    originalDataButton: QPushButton
    newDataButton: QPushButton
    lockHistograms: QCheckBox

    def __init__(self, original_stack: ImageStack, new_stack: ImageStack,
                 presenter: StackComparePresenter | StackChoicePresenter, parent: QMainWindow | None):
        super().__init__(parent, "gui/ui/stack_choice_window.ui")

        self.presenter = presenter

        self.setWindowTitle("Choose the stack you want to keep")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Create stacks and place them in the choice window
        self.original_stack = MIImageView(detailsSpanAllCols=True)
        self.original_stack.name = "Original Stack"
        self.original_stack.enable_nan_check(True)

        self.new_stack = MIImageView(detailsSpanAllCols=True)
        self.new_stack.name = "New Stack"
        self.new_stack.enable_nan_check(True)

        self._setup_stack_for_view(self.original_stack, original_stack.data)
        self._setup_stack_for_view(self.new_stack, new_stack.data)

        self.topVerticalOriginal.addWidget(self.original_stack)
        self.topVerticalNew.addWidget(self.new_stack)

        self.shifting_through_images = False
        self.original_stack.sigTimeChanged.connect(self._sync_timelines_for_new_stack_with_old_stack)
        self.new_stack.sigTimeChanged.connect(self._sync_timelines_for_old_stack_with_new_stack)

        # Hook nav buttons into original stack (new stack not needed as the timelines are synced)
        self.leftButton.pressed.connect(self.original_stack.button_stack_left.pressed)
        self.leftButton.released.connect(self.original_stack.button_stack_left.released)
        self.rightButton.pressed.connect(self.original_stack.button_stack_right.pressed)
        self.rightButton.released.connect(self.original_stack.button_stack_right.released)

        # Hook the choice buttons
        self.originalDataButton.clicked.connect(lambda: self.presenter.notify(Notification.CHOOSE_ORIGINAL))
        self.newDataButton.clicked.connect(lambda: self.presenter.notify(Notification.CHOOSE_NEW_DATA))

        # Hooks the lock histograms checkbox
        self.lockHistograms.clicked.connect(lambda: self.presenter.notify(Notification.TOGGLE_LOCK_HISTOGRAMS))

        # Hook ROI button into both stacks
        self.roiButton.clicked.connect(self._toggle_roi)

        # Hook the two plot ROIs together so that any changes are synced
        self.original_stack.roi.sigRegionChanged.connect(self._sync_roi_plot_for_new_stack_with_old_stack)
        self.new_stack.roi.sigRegionChanged.connect(self._sync_roi_plot_for_old_stack_with_new_stack)
        self.original_stack.roi.sigRegionChanged.connect(self.original_stack.roiChanged)
        self.new_stack.roi.sigRegionChanged.connect(self.new_stack.roiChanged)
        self.original_stack.roi.sigRegionChanged.connect(self.original_stack.viewbox.update)
        self.new_stack.roi.sigRegionChanged.connect(self.new_stack.viewbox.update)

        self._sync_both_image_axis()
        self._ensure_range_is_the_same()

        self.choice_made = False
        self.roi_shown = False

    def _ensure_range_is_the_same(self):
        new_range = self.new_stack.ui.histogram.getLevels()
        original_range = self.original_stack.ui.histogram.getLevels()

        # Set Histograms to the same range
        new_max_y = max(new_range[0], new_range[1])
        new_min_y = min(new_range[0], new_range[1])
        original_max_y = max(original_range[0], original_range[1])
        original_min_y = min(original_range[0], original_range[1])
        y_range_min = min(new_min_y, original_min_y)
        y_range_max = max(new_max_y, original_max_y)
        self.new_stack.ui.histogram.vb.setRange(yRange=(y_range_min, y_range_max))
        self.original_stack.ui.histogram.vb.setRange(yRange=(y_range_min, y_range_max))

        # Set ROI to the same range
        self.original_stack.roi.setSize((self.original_stack.image.shape[1], self.original_stack.image.shape[2]))
        self.new_stack.roi.setSize((self.new_stack.image.shape[1], self.new_stack.image.shape[2]))
        self.original_stack.roi.maxBounds = self.original_stack.roi.parentBounds()
        self.new_stack.roi.maxBounds = self.new_stack.roi.parentBounds()

    def _toggle_roi(self):
        if self.roi_shown:
            self.roi_shown = False
            self.original_stack.ui.roiBtn.setChecked(False)
            self.new_stack.ui.roiBtn.setChecked(False)
            self.original_stack.roiClicked()
            self.new_stack.roiClicked()
        else:
            self.roi_shown = True
            self.original_stack.ui.roiBtn.setChecked(True)
            self.new_stack.ui.roiBtn.setChecked(True)
            self.original_stack.roiClicked()
            self.new_stack.roiClicked()

    def _setup_stack_for_view(self, stack: MIImageView, data: np.ndarray):
        stack.setContentsMargins(4, 4, 4, 4)
        stack.setImage(data)
        stack.ui.menuBtn.hide()
        stack.ui.roiBtn.hide()
        stack.button_stack_right.hide()
        stack.button_stack_left.hide()
        details_size_policy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        details_size_policy.setHorizontalStretch(1)
        stack.details.setSizePolicy(details_size_policy)
        self.roiButton.clicked.connect(stack.roiClicked)

    def _sync_roi_plot_for_new_stack_with_old_stack(self):
        self.new_stack.roi.sigRegionChanged.disconnect(self._sync_roi_plot_for_old_stack_with_new_stack)
        self.new_stack.roi.setPos(self.original_stack.roi.pos())
        self.new_stack.roi.setSize(self.original_stack.roi.size())
        self.new_stack.roi.sigRegionChanged.connect(self._sync_roi_plot_for_old_stack_with_new_stack)

    def _sync_roi_plot_for_old_stack_with_new_stack(self):
        self.original_stack.roi.sigRegionChanged.disconnect(self._sync_roi_plot_for_new_stack_with_old_stack)
        self.original_stack.roi.setPos(self.new_stack.roi.pos())
        self.original_stack.roi.setSize(self.new_stack.roi.size())
        self.original_stack.roi.sigRegionChanged.connect(self._sync_roi_plot_for_new_stack_with_old_stack)

    def _sync_timelines_for_new_stack_with_old_stack(self, index, _):
        self.new_stack.sigTimeChanged.disconnect(self._sync_timelines_for_old_stack_with_new_stack)
        self.new_stack.setCurrentIndex(index)
        self.new_stack.sigTimeChanged.connect(self._sync_timelines_for_old_stack_with_new_stack)

    def _sync_timelines_for_old_stack_with_new_stack(self, index, _):
        self.original_stack.sigTimeChanged.disconnect(self._sync_timelines_for_new_stack_with_old_stack)
        self.original_stack.setCurrentIndex(index)
        self.original_stack.sigTimeChanged.connect(self._sync_timelines_for_new_stack_with_old_stack)

    def _sync_both_image_axis(self):
        self.original_stack.view.linkView(ViewBox.XAxis, self.new_stack.view)
        self.original_stack.view.linkView(ViewBox.YAxis, self.new_stack.view)

    def closeEvent(self, e):
        # Confirm exit is actually wanted as it will lead to data loss
        if not self.choice_made:
            response = QMessageBox.warning(self, "Data Loss! Are you sure?",
                                           "You will lose the original stack if you close this window! Are you sure?",
                                           QMessageBox.Ok | QMessageBox.Cancel)
            if response == QMessageBox.Ok:
                self.presenter.notify(Notification.CHOOSE_NEW_DATA)
            else:
                e.ignore()
                return

        self.original_stack.close()
        self.new_stack.close()
        self.presenter = None

    def _set_from_old_to_new(self) -> None:
        """
        Signal triggered when the histograms are locked and the contrast values changed.
        """
        levels: tuple[float, float] = self.original_stack.ui.histogram.getLevels()
        self.new_stack.ui.histogram.setLevels(*levels)

    def _set_from_new_to_old(self) -> None:
        """
        Signal triggered when the histograms are locked and the contrast values changed.
        """
        levels: tuple[float, float] = self.new_stack.ui.histogram.getLevels()
        self.original_stack.ui.histogram.setLevels(*levels)

    def connect_histogram_changes(self):
        self._set_from_old_to_new()

        self.original_stack.ui.histogram.sigLevelsChanged.connect(self._set_from_old_to_new)
        self.new_stack.ui.histogram.sigLevelsChanged.connect(self._set_from_new_to_old)

        self.new_stack.ui.histogram.vb.linkView(ViewBox.YAxis, self.original_stack.ui.histogram.vb)
        self.new_stack.ui.histogram.vb.linkView(ViewBox.XAxis, self.original_stack.ui.histogram.vb)

    def disconnect_histogram_changes(self):
        self.original_stack.ui.histogram.sigLevelsChanged.disconnect(self._set_from_old_to_new)
        self.new_stack.ui.histogram.sigLevelsChanged.disconnect(self._set_from_new_to_old)

        self.new_stack.ui.histogram.vb.linkView(ViewBox.YAxis, None)
        self.new_stack.ui.histogram.vb.linkView(ViewBox.XAxis, None)
