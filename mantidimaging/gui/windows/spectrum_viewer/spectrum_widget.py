# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal, Qt, QSignalBlocker, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog, QAction, QMenu, QSplitter, QWidget, QVBoxLayout

from pyqtgraph import ROI, GraphicsLayoutWidget, LinearRegionItem, PlotItem, mkPen, ViewBox

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401   # pragma: no cover

if TYPE_CHECKING:
    import numpy as np


class SpectrumROI(ROI):
    """
    Spectrum ROI object subclassed from pyqtgraph ROI containing ROI and associated data.

    @param name: Name of the ROI
    @param sensible_roi: Sensible ROI object containing the ROI data
    @param args: Arguments to pass to the ROI object
    @param kwargs: Keyword arguments to pass to the ROI object
    """
    sig_colour_change = pyqtSignal(str, tuple)

    def __init__(self, name: str, sensible_roi: SensibleROI, *args, **kwargs) -> None:
        kwargs["pos"] = sensible_roi.left, sensible_roi.top
        kwargs["size"] = sensible_roi.width, sensible_roi.height
        super().__init__(*args, **kwargs)
        self._name = name
        self._colour = (0, 0, 0, 255)
        self.maxBounds = self.parentBounds()
        self.addScaleHandle([1, 1], [0, 0])
        self.addScaleHandle([1, 0], [0, 1])
        self.addScaleHandle([0, 0], [1, 1])
        self.addScaleHandle([0, 1], [1, 0])
        self._selected_row = None
        self.roi.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

        self.menu = QMenu()
        self.change_color_action = QAction("Change ROI Colour", self)
        self.change_color_action.triggered.connect(self.onChangeColor)
        self.menu.addAction(self.change_color_action)

    def onChangeColor(self) -> None:
        current_color = QColor(*self._colour)
        selected_color = self.openColorDialog(current_color)
        color_valid = self.check_color_valid(selected_color)
        if color_valid:
            new_color = (selected_color.red(), selected_color.green(), selected_color.blue(), 255)
            self._colour = new_color
            self.sig_colour_change.emit(self._name, new_color)

    def openColorDialog(self, current_color: QColor) -> QColor:
        return QColorDialog.getColor(current_color)

    def check_color_valid(self, get_colour: QColor) -> bool:
        return get_colour.isValid()

    def contextMenuEnabled(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @property
    def roi(self) -> ROI:
        return self

    @property
    def colour(self) -> tuple[int, int, int, int]:
        return self._colour

    @colour.setter
    def colour(self, colour: tuple[int, int, int, int]) -> None:
        self._colour = colour
        self.setPen(self._colour)
        self.hoverPen = mkPen(self._colour, width=3)

    def set_visibility(self, visible: bool) -> None:
        """
        Set the visibility of the ROI and its handles.
        """
        self.setVisible(visible)
        for handle in self.getHandles():
            handle.setVisible(visible)

    @property
    def selected_row(self) -> int | None:
        return self._selected_row

    def adjust_spec_roi(self, roi: SensibleROI) -> None:
        self.setPos((roi.left, roi.top))
        self.setSize((roi.width, roi.height))

    def rename_roi(self, new_name: str) -> None:
        self._name = new_name


class SpectrumWidget(QWidget):
    """
    The widget containing the spectrum plot and the image projection.

    @param parent: The parent widget
    """
    image: MIMiniImageView
    spectrum: PlotItem

    range_control: LinearRegionItem
    roi_dict: dict[str, ROI]
    last_clicked_roi: str

    range_changed = pyqtSignal(object)
    roi_clicked = pyqtSignal(object)
    roi_changed = pyqtSignal()
    roiColorChangeRequested = pyqtSignal(str, tuple)

    spectrum_plot_widget: SpectrumPlotWidget
    image_widget: SpectrumProjectionWidget

    def __init__(self, main_window: MainWindowView) -> None:
        super().__init__()

        self.vbox = QVBoxLayout(self)

        self.image_widget = SpectrumProjectionWidget(main_window)
        self.image = self.image_widget.image
        self.spectrum_plot_widget = SpectrumPlotWidget()
        self.spectrum = self.spectrum_plot_widget.spectrum
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.image_widget)
        self.splitter.addWidget(self.spectrum_plot_widget)
        self.vbox.addWidget(self.splitter)
        widget_height = self.frameGeometry().height()
        self.splitter.setSizes([int(0.7 * widget_height), int(0.3 * widget_height)])

        self.spectrum_data_dict: dict[str, np.ndarray | None] = {}

        self.roi_dict: dict[str, ROI] = {}
        self.colour_index = 0

    def cleanup(self) -> None:
        self.image.cleanup()

    def colour_generator(self) -> tuple[int, int, int, int]:
        """
        A random colour generator to colour ROIs boarders.
        Generates colours that are easy to see for colour blind people if colour_blind_friendly is True.
        By default colour_blind_friendly is set to False

        @return: A random colour in RGBA format. (0-255, 0-255, 0-255, 0-255)
        """
        accessible_colours = [(255, 194, 10), (153, 79, 0), (64, 176, 166), (230, 97, 0), (93, 58, 155), (26, 255, 26),
                              (12, 123, 220), (254, 254, 98), (211, 95, 183), (220, 50, 43)]
        if self.colour_index == len(accessible_colours):
            self.colour_index = 0
        colour = accessible_colours[self.colour_index]
        self.colour_index += 1
        return colour + (255, )

    def change_roi_colour(self, name: str, colour: tuple[int, int, int, int]) -> None:
        """
        Change the colour of an existing ROI
        """
        self.roi_dict[name].colour = colour

    def set_roi_visibility_flags(self, name: str, visible: bool) -> None:
        """
        Change the visibility of an existing ROI including handles and update
        the ROI dictionary.

        @param name: The name of the ROI.
        @param visible: The new visibility of the ROI.
        """
        self.roi_dict[name].set_visibility(visible)

    def get_list_of_roi_names(self) -> list[str]:
        """
        Return a list of all ROI names currently in the widget.
        """
        return list(self.roi_dict.keys())

    def generate_new_roi_name(self) -> str:
        """
        Generate a unique name for a new ROI.
        """
        base_name = "roi"
        existing_names = self.roi_dict.keys()
        index = 1
        while f"{base_name}_{index}" in existing_names:
            index += 1
        return f"{base_name}_{index}"

    def add_new_roi(self, name: str) -> SensibleROI:
        """
        Add a new ROI to the SpectrumWidget.

        @param name: The name of the new ROI.
        @return: The created SensibleROI.
        """
        # Get the image dimensions for ROI
        image_shape = self.image.image_data.shape if self.image.image_data is not None else (1, 1)
        left, top, right, bottom = 0, 0, image_shape[1], image_shape[0]
        default_roi = SensibleROI.from_list([left, top, right, bottom])
        self.add_roi(default_roi, name)

        return default_roi

    def redraw_spectrum(self, name: str) -> None:

        roi = self.spectrum_widget.get_roi(name)
        spectrum = self.model.get_spectrum(roi, self.spectrum_mode, self.view.shuttercount_norm_enabled())
        self.view.set_spectrum(name, spectrum)

    def get_roi_names(self) -> list[str]:
        """
        Returns a list of all ROI names currently in the widget.
        """
        return list(self.roi_dict.keys())

    def do_remove_roi(self, roi_name: str | None = None) -> None:
        """
        Remove a given ROI from the table by ROI name or all ROIs if no name is provided.
        """
        if roi_name is None:
            self.view.spectrum_widget.roi_dict.clear()
        else:
            self.view.spectrum_widget.remove_roi(roi_name)
        self.view.clear_spectrum_data(roi_name)

    def add_roi(self, roi: SensibleROI, name: str | None = None) -> str:
        """
        Add an ROI to the image view.

        @param roi: The ROI to add.
        @param name: The name of the ROI. If None, a new unique name will be generated.
        @return: The name of the added ROI.
        """
        if name is None:
            name = f"roi_{len(self.roi_dict)}"
        roi_object = SpectrumROI(name, roi, rotatable=False, scaleSnap=True, translateSnap=True)
        roi_object.colour = self.colour_generator()
        roi_object.sig_colour_change.connect(lambda name, color: self.roiColorChangeRequested.emit(name, color))
        self.roi_dict[name] = roi_object.roi
        self.image.vb.addItem(self.roi_dict[name])
        self.roi_dict[name].hoverPen = mkPen(self.roi_dict[name].colour, width=3)
        return name

    def adjust_roi(self, new_roi: SensibleROI, roi_name: str) -> None:
        """
        Adjust the existing ROI with the given name.
        @param new_roi: The new SpectrumROI to replace the existing SpectrumROI
        @param roi_name: The name of the existing ROI.
        """
        self.roi_dict[roi_name].adjust_spec_roi(new_roi)

    def adjust_spec_roi(self, roi: SensibleROI) -> None:
        self.setPos((roi.left, roi.top))
        self.setSize((roi.width, roi.height))

    def get_roi(self, roi_name: str) -> SensibleROI:
        """
        Get the ROI with the given name. If no name is given, the default ROI is returned.
        If the name is "all", return a SensibleROI covering the entire image.

        @param roi_name: The name of the ROI to return.
        @return: The ROI with the given name.
        """
        if roi_name in self.roi_dict.keys():
            pos = CloseEnoughPoint(self.roi_dict[roi_name].pos())
            size = CloseEnoughPoint(self.roi_dict[roi_name].size())
            return SensibleROI.from_points(pos, size)
        elif roi_name == "all":
            pos = CloseEnoughPoint((0, 0))
            size = CloseEnoughPoint(self.max_roi_size)
            return SensibleROI.from_points(pos, size)
        else:
            raise KeyError(f"ROI with name {roi_name} does not exist in self.roi_dict or and is not 'all'")

    def remove_roi(self, roi_name: str) -> None:
        """
        Remove a given ROI by name unless it is 'roi' or 'all'.

        @param roi_name: The name of the ROI to remove.
        """
        if roi_name in self.roi_dict.keys() and roi_name != "all":
            self.image.vb.removeItem(self.roi_dict[roi_name])
            del self.roi_dict[roi_name]

    def remove_all_rois(self) -> None:
        """
        Remove all ROIs from the spectrum widget and clear the ROI dictionary.
        """
        for roi_name in list(self.roi_dict.keys()):
            self.remove_roi(roi_name)
        self.roi_dict.clear()
        self.spectrum_data_dict.clear()

    def rename_roi(self, old_name: str, new_name: str) -> None:
        """
        Rename a given ROI and corresponding spectrum by name
        unless it is called 'roi' or 'all'

        @param old_name: The name of the ROI to rename.
        @param new_name: The new name of the ROI.
        @raise KeyError: If the new name is already in use or equal to 'roi' or 'all'.
        """
        if old_name in self.roi_dict.keys() and new_name not in self.roi_dict.keys():
            self.roi_dict[new_name] = self.roi_dict.pop(old_name)
            self.spectrum_data_dict[new_name] = self.spectrum_data_dict.pop(old_name)
            self.roi_dict[new_name].rename_roi(new_name)


class CustomViewBox(ViewBox):

    def __init__(self, *args, **kwds) -> None:
        # kwds['enableMenu'] = False
        ViewBox.__init__(self, *args, **kwds)
        self.setMouseMode(self.PanMode)

    def keyPressEvent(self, event: QEvent) -> None:
        if event.key() == Qt.Key_Control:
            self.setMouseMode(self.RectMode)
            for child in self.allChildren():
                if isinstance(child, LinearRegionItem):
                    child.setMovable(False)
                elif isinstance(child, SpectrumROI):
                    child.translatable = False

    def keyReleaseEvent(self, event: QEvent) -> None:
        if event.key() == Qt.Key_Control:
            self.rbScaleBox.hide()
            self.setMouseMode(self.PanMode)
            for child in self.allChildren():
                if isinstance(child, LinearRegionItem):
                    child.setMovable(True)
                elif isinstance(child, SpectrumROI):
                    child.translatable = True

    ## reimplement right-click to zoom out
    def mouseClickEvent(self, ev: QEvent) -> None:
        if ev.button() == Qt.MouseButton.RightButton and not self.menuEnabled():
            self.autoRange()
        else:
            ViewBox.mouseClickEvent(self, ev)

    ## reimplement mouseDragEvent to disable continuous axis zoom
    def mouseDragEvent(self, ev: QEvent, axis: int | None = None) -> None:
        if axis is not None and ev.button() == Qt.MouseButton.RightButton:
            ev.ignore()
        elif ev.button() == Qt.MouseButton.LeftButton:
            ViewBox.mouseDragEvent(self, ev)
        else:
            ViewBox.mouseDragEvent(self, ev, axis=axis)


class SpectrumPlotWidget(GraphicsLayoutWidget):

    spectrum: PlotItem
    range_control: LinearRegionItem
    range_changed = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()

        self.spectrum_viewbox = CustomViewBox(enableMenu=True)
        self.spectrum = self.addPlot(viewBox=self.spectrum_viewbox)
        self.nextRow()
        self._tof_range_label = self.addLabel()
        self.nextRow()
        self._image_index_range_label = self.addLabel()
        self.range_control = LinearRegionItem()
        self.range_control.sigRegionChangeFinished.connect(self._handle_tof_range_changed)
        self.ci.layout.setRowStretchFactor(0, 1)

    def get_tof_range(self) -> tuple[float, float]:
        r_min, r_max = self.range_control.getRegion()
        return float(r_min), float(r_max)

    def _handle_tof_range_changed(self) -> None:
        tof_range = self.get_tof_range()
        self.set_tof_range_label(tof_range[0], tof_range[1])
        self.range_changed.emit(tof_range)

    def add_range(self, range_min: int | float, range_max: int | float) -> None:
        with QSignalBlocker(self.range_control):
            self.range_control.setBounds((range_min, range_max))
            self.range_control.setRegion((range_min, range_max))
        self.spectrum.addItem(self.range_control)
        self.set_tof_range_label(range_min, range_max)

    def set_tof_range_label(self, range_min: float, range_max: float) -> None:
        self._tof_range_label.setText(f'Range: {range_min:.3f} - {range_max:.3f}')

    def set_image_index_range_label(self, range_min: int, range_max: int) -> None:
        self._image_index_range_label.setText(f'Image index range: {range_min} - {range_max}')

    def set_tof_axis_label(self, tof_axis_label: str) -> None:
        self.spectrum.setLabel('bottom', text=tof_axis_label)


class SpectrumProjectionWidget(GraphicsLayoutWidget):
    image: MIMiniImageView

    def __init__(self, main_window: MainWindowView) -> None:
        super().__init__()
        self.image = MIMiniImageView(name="Projection", view_box_type=CustomViewBox)
        self.addItem(self.image, 0, 0)
        self.ci.layout.setRowStretchFactor(0, 3)

        nan_check_menu = [("Crop Coordinates", lambda: main_window.presenter.show_operation("Crop Coordinates")),
                          ("NaN Removal", lambda: main_window.presenter.show_operation("NaN Removal"))]
        self.image.enable_nan_check(actions=nan_check_menu)
