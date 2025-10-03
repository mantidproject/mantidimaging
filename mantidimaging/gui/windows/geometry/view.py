# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations
from typing import TYPE_CHECKING

from uuid import UUID

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
    QComboBox,
    QPushButton,
    QStackedWidget,
    QApplication,
    QStyle,
)

import matplotlib
from matplotlib import pyplot
from matplotlib.figure import Figure

from mantidimaging.core.data.geometry import GeometryType

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView
from mantidimaging.gui.windows.geometry.presenter import GeometryWindowPresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401  # pragma: no cover


class CustomRangeSpinBox(QDoubleSpinBox):

    def __init__(self, min: int = -10000, max: int = 10000, parent=None):
        super().__init__(parent)
        self.setRange(min, max)


class GeometryWindowView(BaseMainWindowView):

    def __init__(self, main_window: MainWindowView):
        super().__init__(parent=None)

        self.main_window = main_window
        self.presenter = GeometryWindowPresenter(self, main_window)

        self._init_window()
        self._init_widgets()
        self._init_layout()

        self._init_stack_selector()
        self._init_connect_signals()

    def _init_window(self) -> None:
        self.setWindowTitle("Geometry")
        self.resize(1300, 800)

    def _init_widgets(self) -> None:
        self.stackSelector = DatasetSelectorWidgetView(self)

        self.geometryPagesWidget = QStackedWidget()

        self.typeDisplay = QLabel("N/A")
        self.angleDisplay = QLabel("N/A")
        self.corSpinBox = CustomRangeSpinBox()
        self.tiltSpinBox = CustomRangeSpinBox(-45, 45)
        self.sourcePosBox = CustomRangeSpinBox()
        self.detectorPosBox = CustomRangeSpinBox()
        self.conversionTypeSelector = QComboBox()
        self.convertGeometryButton = QPushButton("Convert")

        # New Geometry page

        self.geomTypeSelector = QComboBox()
        self.minAngleSpinBox = CustomRangeSpinBox(-360, 360)
        self.maxAngleSpinBox = CustomRangeSpinBox(-360, 360)
        self.loadAnglesButton = QPushButton("Load Angles from File")
        self.newCorSpinBox = CustomRangeSpinBox()
        self.newTiltSpinBox = CustomRangeSpinBox(-45, 45)
        self.newSourcePosBox = CustomRangeSpinBox()
        self.newDetectorPosBox = CustomRangeSpinBox()
        self.createGeometryButton = QPushButton("Create Geometry")

        self.figureCanvas = FigureCanvas()

    def _init_layout(self) -> None:
        central_container = QWidget(self)
        central_layout = QHBoxLayout(central_container)

        central_layout.addWidget(self._build_left_pane())
        central_layout.addWidget(self._build_plot_visualiser())

        self.setCentralWidget(central_container)

    def _build_left_pane(self) -> QWidget:
        left_scroll_area = QScrollArea()
        left_scroll_area.setFrameShape(QFrame.NoFrame)
        left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll_area.setWidgetResizable(True)
        left_scroll_area.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)

        left_layout.addWidget(self._build_imagestack_selector_group())
        left_layout.addWidget(self._build_geometry_pages_widget())
        left_layout.addStretch()

        left_scroll_area.setWidget(left_container)
        return left_scroll_area

    def _build_imagestack_selector_group(self) -> QWidget:
        stack_selector_group = QGroupBox("Stack")
        stack_selector_layout = QFormLayout(stack_selector_group)
        stack_selector_layout.addRow(self.stackSelector)

        return stack_selector_group

    def _build_geometry_pages_widget(self) -> QWidget:
        self.geometryPagesWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.geometryPagesWidget.addWidget(self._build_geometry_data_display_page())  # page 0 (Geometry exists)
        self.geometryPagesWidget.addWidget(self._build_new_geometry_page())  # page 1 (Geometry doesn't exist)

        return self.geometryPagesWidget

    def _build_geometry_data_display_page(self) -> QWidget:
        data_display_page = QWidget()
        data_display_layout = QVBoxLayout(data_display_page)

        data_display_layout.addWidget(self._build_data_display_group())
        data_display_layout.addWidget(self._build_geometry_conversion_group())
        data_display_layout.addStretch()

        return data_display_page

    def _build_data_display_group(self) -> QWidget:
        data_display_group = QGroupBox("Geometry Data")
        data_display_group.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        data_display_group_layout = QFormLayout(data_display_group)

        data_display_group_layout.addRow(QLabel("Type:"), self.typeDisplay)
        data_display_group_layout.addRow(QLabel("Angles:"), self.angleDisplay)
        data_display_group_layout.addRow(QLabel("COR:"), self.corSpinBox)
        data_display_group_layout.addRow(QLabel("Tilt:"), self.tiltSpinBox)
        data_display_group_layout.addRow(QLabel("Source Pos:"), self.sourcePosBox)
        data_display_group_layout.addRow(QLabel("Detector Pos:"), self.detectorPosBox)

        return data_display_group

    def _build_geometry_conversion_group(self) -> QWidget:
        conversion_group = QGroupBox("Convert Geometry")
        conversion_group.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        conversion_group_layout = QFormLayout(conversion_group)

        for supported_type in GeometryType:
            self.conversionTypeSelector.addItem(supported_type.value)

        conversion_group_layout.addRow(QLabel("To:"), self.conversionTypeSelector)
        conversion_group_layout.addRow(self.convertGeometryButton)

        return conversion_group

    def _build_new_geometry_page(self) -> QWidget:
        new_geometry_page = QWidget()
        new_geometry_layout = QVBoxLayout(new_geometry_page)

        new_geometry_layout.addWidget(self._build_warning_message())
        new_geometry_layout.addWidget(self._build_new_params_group())
        new_geometry_layout.addWidget(self.createGeometryButton)
        new_geometry_layout.addStretch()

        return new_geometry_page

    def _build_warning_message(self) -> QWidget:
        style = QApplication.style()
        font_pt = self.font().pointSizeF()
        icon_size = int(font_pt * 1.8)
        pixmap = style.standardIcon(QStyle.SP_MessageBoxWarning).pixmap(icon_size, icon_size)

        icon = QLabel()
        icon.setPixmap(pixmap)
        icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        text = QLabel("No Geometry for selected stack")
        text.setWordWrap(True)
        text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        warning_message = QWidget()
        warning_layout = QHBoxLayout(warning_message)
        warning_layout.setContentsMargins(4, 2, 4, 2)
        warning_layout.setSpacing(8)
        warning_layout.addWidget(icon)
        warning_layout.addWidget(text)

        return warning_message

    def _build_new_params_group(self) -> QWidget:
        new_params_group = QGroupBox("New Geometry")
        new_params_layout = QFormLayout(new_params_group)

        for supported_type in GeometryType:
            self.geomTypeSelector.addItem(supported_type.value)

        new_params_layout.addRow(QLabel("Type:"), self.geomTypeSelector)
        new_params_layout.addRow(self._build_angle_range_container())
        new_params_layout.addRow(QLabel(""), self.loadAnglesButton)
        new_params_layout.addRow(QLabel("COR:"), self.newCorSpinBox)
        new_params_layout.addRow(QLabel("Tilt:"), self.newTiltSpinBox)
        new_params_layout.addRow(QLabel("Source Position:"), self.newSourcePosBox)
        new_params_layout.addRow(QLabel("Detector Position:"), self.newDetectorPosBox)

        return new_params_group

    def _build_angle_range_container(self) -> QWidget:
        angle_range_container = QWidget()
        angle_range_layout = QHBoxLayout(angle_range_container)

        angle_range_layout.addWidget(QLabel("Min"))
        angle_range_layout.addWidget(self.minAngleSpinBox)
        angle_range_layout.addWidget(QLabel("Max"))
        angle_range_layout.addWidget(self.maxAngleSpinBox)

        return angle_range_container

    def _build_plot_visualiser(self) -> QWidget:
        plot_visualiser = QWidget()
        visualiser_layout = QVBoxLayout(plot_visualiser)
        visualiser_layout.addWidget(self.figureCanvas)
        # visualiser_layout.addWidget(self.figureToolbar)

        return plot_visualiser

    def _init_stack_selector(self) -> None:
        # These stackSelector operations need to happen in this order
        self.stackSelector.presenter.show_stacks = True
        self.stackSelector.stack_selected_uuid.connect(self.presenter.handle_stack_changed)
        self.stackSelector.subscribe_to_main_window(self.main_window)
        self.stackSelector.select_eligible_stack()

    def _init_connect_signals(self) -> None:
        self.corSpinBox.valueChanged.connect(self.presenter.handle_parameter_updates)
        self.tiltSpinBox.valueChanged.connect(self.presenter.handle_parameter_updates)
        self.detectorPosBox.valueChanged.connect(self.presenter.handle_parameter_updates)
        self.sourcePosBox.valueChanged.connect(self.presenter.handle_parameter_updates)
        self.createGeometryButton.clicked.connect(self.presenter.handle_create_new_geometry)
        self.convertGeometryButton.clicked.connect(self.presenter.handle_convert_geometry)

    def set_widget_stack_page(self, index: int) -> None:
        self.geometryPagesWidget.setCurrentIndex(index)

    def refresh_plot(self, figure: Figure) -> None:
        # Clear the plot otherwise pyplot retains the previous figure, leaking memory
        self.clear_plot()
        figure.set_canvas(self.figureCanvas)

        self.figureCanvas.figure = figure
        self.figureCanvas.draw_idle()

        # Trigger a window resize to force the FigureCanvas to correct its size
        old_size = self.size()
        self.adjustSize()
        self.resize(old_size)

    def clear_plot(self) -> None:
        if self.figureCanvas.figure is not None:
            pyplot.close(self.figureCanvas.figure)
            self.figureCanvas.figure.clear()
            self.figureCanvas.draw_idle()

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
    def source_position(self) -> float:
        return self.sourcePosBox.value()

    @source_position.setter
    def source_position(self, value) -> None:
        self.sourcePosBox.setValue(value)

    @property
    def detector_position(self) -> float:
        return self.detectorPosBox.value()

    @detector_position.setter
    def detector_position(self, value) -> None:
        self.detectorPosBox.setValue(value)

    @property
    def new_type(self) -> str:
        return self.geomTypeSelector.currentText()

    @property
    def new_min_angle(self) -> float:
        return self.minAngleSpinBox.value()

    @new_min_angle.setter
    def new_min_angle(self, value) -> None:
        self.minAngleSpinBox.setValue(value)

    @property
    def new_max_angle(self) -> float:
        return self.maxAngleSpinBox.value()

    @new_max_angle.setter
    def new_max_angle(self, value) -> None:
        self.maxAngleSpinBox.setValue(value)

    @property
    def new_rotation_axis(self) -> float:
        return self.newCorSpinBox.value()

    @new_rotation_axis.setter
    def new_rotation_axis(self, value) -> None:
        self.newCorSpinBox.setValue(value)

    @property
    def new_tilt(self) -> float:
        return self.newTiltSpinBox.value()

    @new_tilt.setter
    def new_tilt(self, value) -> None:
        self.newTiltSpinBox.setValue(value)

    @property
    def new_source_position(self) -> float:
        return self.newSourcePosBox.value()

    @new_source_position.setter
    def new_source_position(self, value) -> None:
        self.newSourcePosBox.setValue(value)

    @property
    def new_detector_position(self) -> float:
        return self.newDetectorPosBox.value()

    @new_detector_position.setter
    def new_detector_position(self, value) -> None:
        self.newDetectorPosBox.setValue(value)

    @property
    def conversion_type(self) -> str:
        return self.conversionTypeSelector.currentText()
