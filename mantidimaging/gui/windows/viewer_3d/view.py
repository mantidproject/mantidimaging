# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QVBoxLayout, QWidget, QMessageBox
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from ccpi.viewer.CILViewer import CILViewer
from ccpi.viewer.utils.conversion import Converter

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

    # Set up the VTK render window interactor and the CIL Viewer
    def _init_viewer(self):
        self.vtk_widget = QVTKRenderWindowInteractor()
        self.viewer = CILViewer(renWin=self.vtk_widget.GetRenderWindow(), iren=self.vtk_widget)
        self.vtk_widget.Initialize()

    # Set up the central widget and layout, and add the viewer
    def _init_layout(self):
        self.central_widget = QWidget(self)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.vtk_widget)
        self.layout.addWidget(self.stackSelector)
        self.setCentralWidget(self.central_widget)

    # Set up the stack selector widget
    def _init_stack_selector(self) -> None:
        self.stackSelector.presenter.show_stacks = True
        self.stackSelector.stack_selected_uuid.connect(self.presenter.handle_stack_change)
        self.stackSelector.subscribe_to_main_window(self.main_window)
        self.stackSelector.select_eligible_stack()

    # Update the viewer with a new numpy image array, initialise and render it
    def _update_viewer(self, numpy_image: np.ndarray):
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

    # Set window properties
    def _init_window(self):
        self.setWindowTitle("Mantid Imaging - 3D Viewer")
        self.resize(800, 600)
        self.show()

    # Clean up VTK resources on close
    def _cleanup_resources(self, event):
        self.stackSelector.unsubscribe_from_main_window()
        self.vtk_widget.Finalize()
        print("VTK resources finalized.")
        super().closeEvent(event)

    @property
    def current_stack(self) -> UUID:
        current = self.stackSelector.current()
        if current is None:
            raise ValueError("No stack is currently selected.")
        return current
