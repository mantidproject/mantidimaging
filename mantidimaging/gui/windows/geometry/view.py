# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations
from typing import TYPE_CHECKING

import io
from uuid import UUID

import numpy

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QScrollArea,
    QFrame,
    QWidget,
    QVBoxLayout,
    QDoubleSpinBox,
    QLabel,
    QGroupBox,
    QFormLayout,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
    QComboBox,
    QPushButton,
    QStackedWidget,
)
from pyqtgraph.dockarea.Container import StackedWidget

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView
from mantidimaging.gui.windows.geometry.presenter import GeometryWindowPresenter

## EXPERIMENTAL
import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qtagg import (FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as
                                               NavigationToolbar)
from matplotlib.figure import Figure

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover


class GeometryWindowView(BaseMainWindowView):

    def __init__(self, main_window: MainWindowView):
        # super().__init__(None, 'gui/ui/geometry_window.ui')
        super().__init__(parent=None)

        self.main_window = main_window
        self.presenter = GeometryWindowPresenter(self, main_window)

        self._init_window()
        self._init_widgets()
        self._init_layout()
        self._connect_signals()

    def _init_window(self) -> None:
        self.setWindowTitle("Geometry")
        self.resize(1300, 800)

    def _init_widgets(self) -> None:
        ## Parameters pane

        self.stackSelector = DatasetSelectorWidgetView(self)

        self.stackedWidget = QStackedWidget()

        # Parameters page

        self.typeDisplay = QLabel("N/A")
        self.angleDisplay = QLabel("N/A")
        self.corSpinBox = QDoubleSpinBox()
        self.tiltSpinBox = QDoubleSpinBox()

        # New Geometry page

        self.typeSelector = QComboBox()
        self.minAngleSpinBox = QDoubleSpinBox()
        self.maxAngleSpinBox = QDoubleSpinBox()
        self.loadAnglesButton = QPushButton("Load Angles from File")
        self.newCorSpinBox = QDoubleSpinBox()
        self.newTiltSpinBox = QDoubleSpinBox()
        self.createGeometryButton = QPushButton("Create Geometry")

        ## Visualiser pane

        self.figureCanvas = FigureCanvas()
        self.figureToolbar = NavigationToolbar(self.figureCanvas, self)

    def _init_layout(self) -> None:
        central_container = QWidget()
        self.setCentralWidget(central_container)
        main_layout = QHBoxLayout(central_container)

        main_layout.addWidget(self._build_left_pane())
        main_layout.addWidget(self._build_plot_visualiser())

    def _build_left_pane(self) -> QWidget:
        left_scroll_area = QScrollArea()
        left_scroll_area.setFrameShape(QFrame.NoFrame)
        left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll_area.setWidgetResizable(True)

        left_container = QWidget()
        left_scroll_area.setWidget(left_container)

        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(9, 9, 9, 9)
        left_layout.setSpacing(9)

        self.stackedWidget.addWidget(self._build_parameters_page())  # page 0 (Geometry exists)
        self.stackedWidget.addWidget(self._build_new_geometry_page())  # page 1 (Geometry doesn't exist)
        self.stackedWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        left_layout.addWidget(self._build_data_group())
        left_layout.addWidget(self.stackedWidget)
        left_layout.addStretch()

        return left_scroll_area

    def _build_data_group(self) -> QWidget:
        data_group = QGroupBox("Data")
        data_layout = QFormLayout(data_group)
        data_layout.addRow(self.stackSelector)

        self.stackSelector.presenter.show_stacks = True
        self.stackSelector.stack_selected_uuid.connect(self.presenter.handle_stack_changed)
        self.stackSelector.subscribe_to_main_window(self.main_window)
        # self.stackSelector.stack_selected_uuid.connect(lambda: self.presenter.notify(PresN.SET_CURRENT_STACK))
        self.stackSelector.select_eligible_stack()

        return data_group

    def _build_parameters_page(self) -> QWidget:
        params_group = QGroupBox("Parameters")
        params_group.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        parameters_layout = QFormLayout(params_group)
        # parameters_layout.setContentsMargins(9, 9, 9, 9)
        parameters_layout.addRow(QLabel("Type:"), self.typeDisplay)
        parameters_layout.addRow(QLabel("Angles:"), self.angleDisplay)
        parameters_layout.addRow(QLabel("COR:"), self.corSpinBox)
        parameters_layout.addRow(QLabel("Tilt:"), self.tiltSpinBox)

        return params_group

    def _build_new_geometry_page(self) -> QWidget:
        new_geometry_page = QWidget()
        new_geometry_page.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        new_geometry_page_layout = QVBoxLayout(new_geometry_page)

        self.typeSelector.addItem("Parallel 3D")
        self.typeSelector.addItem("Conebeam 3D")

        new_geometry_group = QGroupBox("New Geometry")
        new_geometry_form = QFormLayout(new_geometry_group)
        new_geometry_form.addRow(QLabel("Type:"), self.typeSelector)
        #new_geometry_form.addRow()
        new_geometry_form.addRow(QLabel("Angles:"), QLabel("Min: - Max:"))
        new_geometry_form.addRow(self.loadAnglesButton)
        #new_geometry_form.addRow()
        new_geometry_form.addRow(QLabel("COR:"), self.newCorSpinBox)
        new_geometry_form.addRow(QLabel("Tilt:"), self.newTiltSpinBox)

        new_geometry_page_layout.addWidget(QLabel("! No Geometry for selected stack"))
        new_geometry_page_layout.addWidget(new_geometry_group)
        new_geometry_page_layout.addWidget(self.createGeometryButton)

        return new_geometry_page

    def _build_plot_visualiser(self) -> QWidget:
        plot_visualiser = QWidget()
        image_layout = QVBoxLayout(plot_visualiser)
        image_layout.setSpacing(0)
        image_layout.setSizeConstraint(image_layout.SetMaximumSize)

        image_layout.addWidget(self.figureCanvas)
        image_layout.addWidget(self.figureToolbar)

        return plot_visualiser

    def _connect_signals(self) -> None:
        self.createGeometryButton.clicked.connect(self.presenter.handle_create_geometry)
        self.corSpinBox.valueChanged.connect(self.presenter.handle_parameter_updates)
        self.tiltSpinBox.valueChanged.connect(self.presenter.handle_parameter_updates)

    def set_widget_stack_page(self, index: int) -> None:
        self.stackedWidget.setCurrentIndex(index)

        page = self.stackedWidget.widget(index)
        if not page:
            return
        hint = page.sizeHint()
        self.stackedWidget.setMinimumSize(hint)
        # self.stackedWidget.setFixedSize(self.stackedWidget.)
        self.stackedWidget.updateGeometry()
        self.stackedWidget.adjustSize()

    def update_plot(self, figure: Figure) -> None:
        self.figureCanvas.figure.clear()
        self.figureCanvas.figure = figure
        figure.set_canvas(self.figureCanvas)
        self.figureCanvas.draw_idle()

    def clear_plot(self) -> None:
        self.figureCanvas.figure.clear()
        self.figureCanvas.draw()

    @property
    def current_stack(self) -> UUID | None:
        return self.stackSelector.current()

    @property
    def type(self) -> str:
        return self.typeDisplay.text()

    @type.setter
    def type(self, value):
        self.typeDisplay.setText(value)

    @property
    def angles(self) -> str:
        return self.angleDisplay.text()

    @angles.setter
    def angles(self, value) -> None:
        self.angleDisplay.setText(value)

    @property
    def rotation_axis(self) -> float:
        return self.corSpinBox.value()

    @rotation_axis.setter
    def rotation_axis(self, value) -> None:
        self.corSpinBox.setValue(value)

    @property
    def tilt(self) -> float:
        return self.tiltSpinBox.value()

    @tilt.setter
    def tilt(self, value) -> None:
        self.tiltSpinBox.setValue(value)

    @property
    def new_type(self) -> str:
        return self.typeSelector.currentText()

    @property
    def new_min_angle(self) -> float:
        return self.minAnglesSpinBox.value()

    @new_min_angle.setter
    def new_min_angle(self, value) -> None:
        self.minAnglesSpinBox.setValue(value)

    @property
    def new_max_angle(self) -> float:
        return self.maxAnglesSpinBox.value()

    @new_max_angle.setter
    def new_max_angle(self, value) -> None:
        self.maxAnglesSpinBox.setValue(value)

    @property
    def new_cor(self) -> float:
        return self.newCorSpinBox.value()

    @new_cor.setter
    def new_cor(self, value) -> None:
        self.newCorSpinBox.setValue(value)

    @property
    def new_tilt(self) -> float:
        return self.newTiltSpinBox.value()

    @new_tilt.setter
    def new_tilt(self, value) -> None:
        self.newTiltSpinBox.setValue(value)
