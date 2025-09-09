# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from ccpi.viewer.CILViewer import CILViewer


class MI3DViewer(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set up the central widget and layout
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Set up the VTK render window interactor
        self.vtk_widget = QVTKRenderWindowInteractor(central_widget)

        # Set up the CIL Viewer
        self.viewer = CILViewer(renWin=self.vtk_widget.GetRenderWindow(), iren=self.vtk_widget)

        # Add the VTK widget to the layout
        layout.addWidget(self.vtk_widget)
        self.setCentralWidget(central_widget)

        # Initialize the VTK widget
        self.vtk_widget.Initialize()

        # Set window properties
        self.setWindowTitle("Mantid Imaging - 3D Viewer")
        self.resize(800, 600)
        self.show()

    def closeEvent(self, event):
        # Clean up VTK resources
        self.vtk_widget.Finalize()
        super().closeEvent(event)
