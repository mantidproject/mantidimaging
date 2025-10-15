# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import QTimer
from ccpi.viewer.utils.conversion import Converter

from ccpi.viewer.QCILViewerWidget import QCILViewerWidget
from ccpi.viewer import viewer3D

from .presenter import MI3DViewerPresenter
from logging import getLogger
import numpy as np

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover
    from uuid import UUID

LOG = getLogger(__name__)


class MI3DViewerWindowView(BaseMainWindowView):

    def __init__(self, main_window: MainWindowView):
        super().__init__(parent=None)
        self.main_window = main_window
        self.presenter = MI3DViewerPresenter(self, main_window)
        self.stackSelector = DatasetSelectorWidgetView(self)
        self._init_window()
        self._init_viewer()
        self._init_layout()
        self._init_stack_selector()

    def _init_viewer(self):
        """
        Initialize the embedded QCIL 3D viewer widget.
        """
        self.frame = QCILViewerWidget(parent=self, viewer=viewer3D, shape=(800, 600))
        self.viewer = self.frame.viewer
        self.vtk_widget = self.frame.vtkWidget

        QTimer.singleShot(0, self.vtk_widget.Initialize)

    def _init_layout(self):
        """
        Initialize the layout for the 3D viewer window.
        """
        self.central_widget = QWidget(self)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.frame)
        self.layout.addWidget(self.stackSelector)
        self.setCentralWidget(self.central_widget)

    def _init_stack_selector(self) -> None:
        """
        Initialize the stack selector widget.
        """
        self.stackSelector.presenter.show_stacks = True
        self.stackSelector.stack_selected_uuid.connect(self.presenter.handle_stack_change)
        self.stackSelector.subscribe_to_main_window(self.main_window)
        self.stackSelector.select_eligible_stack()

    def update_viewer(self, numpy_image: np.ndarray):
        """
        Update the 3D viewer with a new numpy image.
        @param numpy_image: The numpy array representing the image data.
        """
        try:
            # COMPAT: CIL: need a manual conversion to work around https://github.com/TomographicImaging/CILViewer/issues/478
            vtkdata = Converter.numpy2vtkImage(numpy_image)
            self.viewer.setInputData(vtkdata)

            self.viewer.installPipeline()
            self.viewer.updatePipeline()
            self.viewer.updateVolumePipeline()
            self.viewer.saveDefaultCamera()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update 3D viewer:\n{e}")

    def _init_window(self):
        self.setWindowTitle("Mantid Imaging - 3D Viewer")
        self.resize(800, 600)
        self.show()

    def _cleanup_resources(self, event):
        """
        Clean up VTK resources on close.
        """
        self.stackSelector.unsubscribe_from_main_window()
        self.vtk_widget.Finalize()
        super().closeEvent(event)

    @property
    def current_stack(self) -> UUID:
        current = self.stackSelector.current()
        if current is None:
            raise ValueError("No stack is currently selected.")
        return current
