# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PyQt5.QtCore import pyqtSignal, Qt
from pyqtgraph import ROI, GraphicsLayoutWidget, LinearRegionItem, PlotItem, mkPen

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView

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

    def __init__(self, name: str, sensible_roi: SensibleROI, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._name = name
        self._colour = (0, 0, 0, 255)
        self.setPos((sensible_roi.left, sensible_roi.top))
        self.setSize((sensible_roi.width, sensible_roi.height))
        self.maxBounds = self.parentBounds()
        self.addScaleHandle([1, 1], [0, 0])
        self.addScaleHandle([1, 0], [0, 1])
        self.addScaleHandle([0, 0], [1, 1])
        self.addScaleHandle([0, 1], [1, 0])
        self._selected_row = None

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

    @property
    def selected_row(self) -> Optional[int]:
        return self._selected_row


class SpectrumWidget(GraphicsLayoutWidget):
    """
    The widget containing the spectrum plot and the image projection.

    @param parent: The parent widget
    """
    image: MIMiniImageView
    spectrum: PlotItem
    range_control: LinearRegionItem
    roi_dict: dict[Optional[str], ROI]

    range_changed = pyqtSignal(object)
    roi_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.image = MIMiniImageView(name="Projection")
        self.addItem(self.image, 0, 0)

        self.nextRow()
        self.spectrum = self.addPlot()

        self.spectrum_data_dict: dict[str, np.ndarray] = {}
        self.nextRow()
        self._tof_range_label = self.addLabel()

        self.ci.layout.setRowStretchFactor(0, 3)
        self.ci.layout.setRowStretchFactor(1, 1)

        self.range_control = LinearRegionItem()
        self.range_control.sigRegionChanged.connect(self._handle_tof_range_changed)

        self.roi_dict: dict[Optional[str], ROI] = {}
        self.colour_index = 0

    def add_range(self, range_min: int, range_max: int):
        self.range_control.setBounds((range_min, range_max))
        self.range_control.setRegion((range_min, range_max))
        self.spectrum.addItem(self.range_control)
        self._set_tof_range_label(range_min, range_max)

    def get_tof_range(self) -> tuple[int, int]:
        r_min, r_max = self.range_control.getRegion()
        return int(r_min), int(r_max)

    def random_colour_generator(self) -> tuple[int, int, int, int]:
        """
        A random colour generator to colour ROIs boarders.
        Generates colours that are easy to see for colour blind people if colour_blind_friendly is True.
        By default colour_blind_friendly is set to False

        @return: A random colour in RGBA format. (0-255, 0-255, 0-255, 0-255)
        """
        accessible_colours = [(255, 194, 10), (12, 123, 220), (153, 79, 0), (64, 176, 166), (230, 97, 0), (93, 58, 155),
                              (26, 255, 26), (254, 254, 98), (211, 95, 183), (220, 50, 43)]
        if self.colour_index == len(accessible_colours):
            self.colour_index = 0
        colour = accessible_colours[self.colour_index]
        self.colour_index += 1
        return colour + (255, )

    def change_roi_colour(self, name: str, colour: tuple[int, int, int, int]) -> None:
        """
        Change the colour of an existing ROI

        @param name: The name of the ROI.
        @param colour: The new colour of the ROI.
        """
        self.roi_dict[name].colour = colour
        self.roi_dict[name].setPen(self.roi_dict[name].colour)

    def set_roi_visibility_flags(self, name: str, visible: bool) -> None:
        """
        Change the visibility of an existing ROI including handles and update
        the ROI dictionary, sending a signal to the main window.

        @param name: The name of the ROI.
        @param visible: The new visibility of the ROI.
        """
        handles = self.roi_dict[name].getHandles()
        for handle in handles:
            handle.setVisible(visible)
        self.roi_dict[name].setVisible(visible)
        self.roi_dict[name].setAcceptedMouseButtons(Qt.NoButton)
        self.roi_dict[name].sigRegionChanged.connect(self.roi_changed.emit)

    def set_roi_alpha(self, name: str, alpha: float) -> None:
        """
        Change the alpha value of an existing ROI

        @param name: The name of the ROI.
        @param alpha: The new alpha value of the ROI.
        """
        self.roi_dict[name].colour = self.roi_dict[name].colour[:3] + (alpha, )
        self.roi_dict[name].setPen(self.roi_dict[name].colour)
        self.roi_dict[name].hoverPen = mkPen(self.roi_dict[name].colour, width=3)
        self.set_roi_visibility_flags(name, bool(alpha))

    def add_roi(self, roi: SensibleROI, name: str) -> None:
        """
        Add an ROI to the image view.

        @param roi: The ROI to add.
        @param name: The name of the ROI.
        """
        roi_object = SpectrumROI(name, roi, pos=(0, 0), rotatable=False, scaleSnap=True, translateSnap=True)
        roi_object.colour = self.random_colour_generator()

        self.roi_dict[name] = roi_object.roi
        self.max_roi_size = roi_object.size()
        self.roi_dict[name].sigRegionChanged.connect(self.roi_changed.emit)
        self.image.vb.addItem(self.roi_dict[name])
        self.roi_dict[name].hoverPen = mkPen(self.roi_dict[name].colour, width=3)

    def get_roi(self, roi_name: str) -> SensibleROI:
        """
        Get the ROI with the given name. If no name is given, the default ROI is returned.

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
            raise KeyError("ROI with name {roi_name} does not exist in self.roi_dict or and is not 'all'".format(
                roi_name=roi_name))

    def _set_tof_range_label(self, range_min: int, range_max: int) -> None:
        self._tof_range_label.setText(f'ToF range: {range_min} - {range_max}')

    def _handle_tof_range_changed(self) -> None:
        tof_range = self.get_tof_range()
        self._set_tof_range_label(tof_range[0], tof_range[1])
        self.range_changed.emit(tof_range)

    def remove_roi(self, roi_name: str) -> None:
        """
        Remove a given ROI by name unless it is 'roi' or 'all'.

        @param roi_name: The name of the ROI to remove.
        """
        if roi_name in self.roi_dict.keys() and roi_name != "all":
            self.image.vb.removeItem(self.roi_dict[roi_name])
            del self.roi_dict[roi_name]

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

    def reset_roi_size(self, image_shape) -> None:
        """
        Reset the size of the ROI to the maximum size of the image.

        @param image_shape: The shape of the image.
        """
        roi_name = list(self.roi_dict.keys())[0]
        height, width = image_shape

        self.roi_dict[roi_name].setSize([width, height])
        self.roi_dict[roi_name].setPos([0, 0])
        self.roi_dict[roi_name].maxBounds = self.roi_dict[roi_name].parentBounds()
        self.image.vb.addItem(self.roi_dict[roi_name])
        self.roi_dict[roi_name].sigRegionChanged.connect(self.roi_changed.emit)
