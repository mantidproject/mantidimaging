from typing import List

import numpy as np
from PyQt5.QtWidgets import QPushButton, QDoubleSpinBox

from mantidimaging.core.data import Images
from mantidimaging.core.utility.data_containers import ScalarCoR, ProjectionAngles, ReconstructionParameters
from mantidimaging.gui.dialogs.cor_inspection.presenter import CORInspectionDialogPresenter
from mantidimaging.gui.dialogs.cor_inspection.recon_slice_view import CompareSlicesView
from mantidimaging.gui.dialogs.cor_inspection.types import ImageType
from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.utility.qt_helpers import BlockQtSignals


class CORInspectionDialogView(BaseDialogView):
    lessButton: QPushButton
    currentButton: QPushButton
    moreButton: QPushButton
    step: QDoubleSpinBox

    def __init__(self, parent, data: Images, slice_index: int, initial_cor: ScalarCoR, proj_angles: ProjectionAngles,
                 recon_params: ReconstructionParameters):
        super().__init__(parent, 'gui/ui/cor_inspection_dialog.ui')
        self.presenter = CORInspectionDialogPresenter(self, data, slice_index, initial_cor, proj_angles, recon_params)

        self.step.editingFinished.connect(lambda: self.presenter.do_update_ui_parameters())
        self.lessButton.clicked.connect(lambda: self.presenter.on_select_image(ImageType.LESS))
        self.currentButton.clicked.connect(lambda: self.presenter.on_select_image(ImageType.CURRENT))
        self.moreButton.clicked.connect(lambda: self.presenter.on_select_image(ImageType.MORE))

        self.finishButton.clicked.connect(self.accept)

        self.image_canvas = CompareSlicesView(self)
        self.imagePlotLayout.addWidget(self.image_canvas)

        self.presenter.do_refresh()
        self.image_canvas.current_hist.imageChanged(autoLevel=True, autoRange=True)

    def set_image(self, image_type: ImageType, recon_data: np.ndarray, title: str):
        self.image_canvas.set_image(image_type, recon_data, title)

    def set_maximum_cor(self, cor):
        """
        Set the maximum valid rotation centre.
        """
        self.step.setMaximum(cor)

    @property
    def step_size(self):
        return self.step.value()

    @step_size.setter
    def step_size(self, value):
        with BlockQtSignals([self.step]):
            self.step.setValue(value)

    @property
    def optimal_rotation_centre(self) -> ScalarCoR:
        return self.presenter.optimal_rotation_centre

    def mark_best_recon(self, diffs):
        best = diffs.index(max(diffs))
        buttons: List[QPushButton] = [self.lessButton, self.currentButton, self.moreButton]

        for b in buttons:
            b.setStyleSheet('')

        buttons[best].setStyleSheet("QPushButton{ background-color:green;}")
