# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import random
from typing import TYPE_CHECKING, Optional

from PyQt5.QtCore import pyqtSignal
from pyqtgraph import ROI, GraphicsLayoutWidget, LinearRegionItem, PlotItem

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView

if TYPE_CHECKING:
    from .view import SpectrumViewerWindowView


class SpectrumWidget(GraphicsLayoutWidget):
    image: MIMiniImageView
    spectrum: PlotItem
    range_control: LinearRegionItem
    roi_dict: dict[Optional[str], ROI]

    range_changed = pyqtSignal(object)
    roi_changed = pyqtSignal()

    def __init__(self, parent: 'SpectrumViewerWindowView'):
        super().__init__(parent)
        self.parent = parent

        self.image = MIMiniImageView(name="Projection", parent=parent)
        self.addItem(self.image, 0, 0)

        self.nextRow()
        self.spectrum = self.addPlot()

        self.nextRow()
        self._tof_range_label = self.addLabel()

        self.ci.layout.setRowStretchFactor(0, 3)
        self.ci.layout.setRowStretchFactor(1, 1)

        self.range_control = LinearRegionItem()
        self.range_control.sigRegionChanged.connect(self._handle_tof_range_changed)

        self.roi_dict = {}

        self.max_roi_size = [0, 0]

    def add_range(self, range_min: int, range_max: int):
        self.range_control.setBounds((range_min, range_max))
        self.range_control.setRegion((range_min, range_max))
        self.spectrum.addItem(self.range_control)
        self._set_tof_range_label(range_min, range_max)

    def get_tof_range(self) -> tuple[int, int]:
        r_min, r_max = self.range_control.getRegion()
        return int(r_min), int(r_max)

    def random_colour_generator(self, colour_blind_friendly: bool = True) -> tuple[int, int, int]:
        """
        A random colour generator to colour ROIs boarders.
        Generates colours that are easy to see for colour blind people if colour_blind_friendly is True.
        By default colour_blind_friendly is set to False

        :param colour_blind_friendly: If True, the colours will be colour blind friendly.

        :return: A random colour in RGB format. (0-255, 0-255, 0-255)
        """
        #  Colour blind friendly pallette
        accessible_colours = [(255, 194, 10), (12, 123, 220), (153, 79, 0), (0, 108, 209), (225, 190, 106),
                              (64, 176, 166), (230, 97, 0), (93, 58, 155), (26, 255, 26), (75, 0, 146), (254, 254, 98),
                              (211, 95, 183), (0, 90, 181), (220, 50, 43), (26, 133, 255), (212, 17, 89)]
        return random.choice(accessible_colours)

    def add_roi(self, roi: SensibleROI, name: str = None) -> None:
        """
        Add an ROI to the image view.

        :param roi: The ROI to add.
        :param name: The name of the ROI.
        """

        my_roi = ROI(pos=(0, 0), rotatable=False, scaleSnap=True, translateSnap=True)
        roi_colour = self.random_colour_generator()
        my_roi.setPen(roi_colour)
        my_roi.setPos((roi.left, roi.top))
        my_roi.setSize((roi.width, roi.height))
        my_roi.maxBounds = my_roi.parentBounds()
        my_roi.addScaleHandle([1, 1], [0, 0])
        my_roi.addScaleHandle([1, 0], [0, 1])
        my_roi.addScaleHandle([0, 0], [1, 1])
        my_roi.addScaleHandle([0, 1], [1, 0])

        self.max_roi_size[0] = roi.width
        self.max_roi_size[1] = roi.height

        self.roi_dict[name] = my_roi
        self.roi_dict[name].sigRegionChanged.connect(self.roi_changed.emit)
        self.image.vb.addItem(self.roi_dict[name])

    def get_roi(self, roi_name: str = None) -> SensibleROI:
        """
        Get the ROI with the given name. If no name is given, the default ROI is returned.

        :param roi_name: The name of the ROI to return.
        :return: The ROI with the given name.
        """
        if roi_name in self.roi_dict.keys():
            pos = CloseEnoughPoint(self.roi_dict[roi_name].pos())
            size = CloseEnoughPoint(self.roi_dict[roi_name].size())
            return SensibleROI.from_points(pos, size)
        elif roi_name == "all":
            pos = CloseEnoughPoint((0, 0))
            size = CloseEnoughPoint((self.max_roi_size[0], self.max_roi_size[1]))
            return SensibleROI.from_points(pos, size)
        else:
            raise KeyError(f"ROI with name {roi_name} does not exist in self.roi_dict or and is not 'all'")

    def _set_tof_range_label(self, range_min: int, range_max: int) -> None:
        self._tof_range_label.setText(f'ToF range: {range_min} - {range_max}')

    def _handle_tof_range_changed(self) -> None:
        tof_range = self.get_tof_range()
        self._set_tof_range_label(tof_range[0], tof_range[1])
        self.range_changed.emit(tof_range)

    def clear_data(self):
        self.image.clear()
        self.spectrum.clear()
        for roi in self.roi_dict:
            self.image.vb.removeItem(roi)

        self._tof_range_label.setText('')
