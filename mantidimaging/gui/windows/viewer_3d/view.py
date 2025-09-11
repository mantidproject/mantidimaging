# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from ccpi.viewer.CILViewer import CILViewer


class MI3DViewer(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_viewer()
        self.init_layout()
        self.init_window()

    # Set up the VTK render window interactor and the CIL Viewer
    def init_viewer(self):
        self.vtk_widget = QVTKRenderWindowInteractor()
        self.viewer = CILViewer(renWin=self.vtk_widget.GetRenderWindow(), iren=self.vtk_widget)
        self.vtk_widget.Initialize()

    # Set up the central widget and layout, and add the viewer
    def init_layout(self):
        self.central_widget = QWidget(self)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.vtk_widget)
        self.setCentralWidget(self.central_widget)

    # Set window properties
    def init_window(self):
        self.setWindowTitle("Mantid Imaging - 3D Viewer")
        self.resize(800, 600)
        self.show()

    # Clean up VTK resources on close
    def closeEvent(self, event):
        self.vtk_widget.Finalize()
        super().closeEvent(event)
