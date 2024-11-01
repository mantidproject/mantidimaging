# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
from PyQt5.QtWidgets import QPushButton, QDoubleSpinBox, QSpinBox, QStackedWidget

from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.data_containers import ScalarCoR, ReconstructionParameters
from mantidimaging.gui.dialogs.cor_inspection.presenter import CORInspectionDialogPresenter
from mantidimaging.gui.dialogs.cor_inspection.recon_slice_view import CompareSlicesView
from mantidimaging.gui.dialogs.cor_inspection.types import ImageType
from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.utility.qt_helpers import BlockQtSignals


class CORInspectionDialogView(BaseDialogView):
    lessButton: QPushButton
    currentButton: QPushButton
    moreButton: QPushButton
    stepCOR: QDoubleSpinBox
    stepIterations: QSpinBox
    stepStackedWidget: QStackedWidget
    instructionStackedWidget: QStackedWidget

    spin_box: QSpinBox | QDoubleSpinBox

    def __init__(self, parent, images: ImageStack, slice_index: int, initial_cor: ScalarCoR,
                 recon_params: ReconstructionParameters, iters_mode: bool):
        super().__init__(parent, 'gui/ui/cor_inspection_dialog.ui')
        self.iters_mode = iters_mode

        if self.iters_mode:
            self.spin_box = self.stepIterations
        else:
            self.spin_box = self.stepCOR

        self.presenter = CORInspectionDialogPresenter(self, images, slice_index, initial_cor, recon_params, iters_mode)

        self.stepCOR.editingFinished.connect(lambda: self.presenter.do_update_ui_parameters())
        self.stepIterations.editingFinished.connect(lambda: self.presenter.do_update_ui_parameters())

        self.lessButton.clicked.connect(lambda: self.presenter.on_select_image(ImageType.LESS))
        self.currentButton.clicked.connect(lambda: self.presenter.on_select_image(ImageType.CURRENT))
        self.moreButton.clicked.connect(lambda: self.presenter.on_select_image(ImageType.MORE))

        self.finishButton.clicked.connect(self.accept)

        self.stepStackedWidget.setCurrentIndex(int(iters_mode))
        self.instructionStackedWidget.setCurrentIndex(int(iters_mode))

        self.image_canvas = CompareSlicesView(self)
        self.imagePlotLayout.addWidget(self.image_canvas)

        self.presenter.do_refresh()

    def set_image(self, image_type: ImageType, recon_data: np.ndarray, title: str) -> None:
        self.image_canvas.set_image(image_type, recon_data, title)

    def set_maximum_cor(self, cor) -> None:
        """
        Set the maximum valid rotation centre.
        """
        self.stepCOR.setMaximum(cor)

    @property
    def step_size(self) -> None:
        return self.spin_box.value()

    @step_size.setter
    def step_size(self, value) -> None:
        with BlockQtSignals([self.spin_box]):
            self.spin_box.setValue(value)

    @property
    def optimal_rotation_centre(self) -> ScalarCoR:
        return self.presenter.optimal_rotation_centre

    @property
    def optimal_iterations(self) -> int | float:
        return self.presenter.optimal_iterations

    def mark_best_recon(self, diffs) -> None:
        best = diffs.index(max(diffs))
        buttons: list[QPushButton] = [self.lessButton, self.currentButton, self.moreButton]

        for b in buttons:
            b.setStyleSheet('')

        buttons[best].setStyleSheet("QPushButton{ background-color:green;}")
