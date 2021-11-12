# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from collections import OrderedDict
from typing import Callable, List, Optional

import numpy as np
from pyqtgraph import ColorMap, ImageItem, ViewBox

from mantidimaging.gui.widgets.indicator_icon.view import IndicatorIconView
from mantidimaging.core.utility import finder

OVERLAY_COLOUR_NAN = [255, 0, 0, 255]
OVERLAY_COLOUR_NONPOSITVE = [255, 192, 0, 255]


class BadDataCheck:
    check_function: Callable[[np.ndarray], np.ndarray]
    indicator: IndicatorIconView

    def __init__(self, check_function, indicator, overlay, color):
        self.check_function = check_function
        self.indicator = indicator
        self.overlay = overlay
        self.color = color
        self.setup_overlay()
        self.indicator.connected_overlay = self.overlay

    def do_check(self, data):
        bad_data = self.check_function(data)
        any_bad = bad_data.any()
        # cast any_bad to python bool to prevent DeprecationWarning
        self.indicator.setVisible(bool(any_bad))

        self.overlay.setImage(bad_data)

    def setup_overlay(self):
        color = np.array([[0, 0, 0, 0], self.color], dtype=np.ubyte)
        color_map = ColorMap([0, 1], color)
        self.overlay.setOpacity(0)
        lut = color_map.getLookupTable(0, 1, 2)
        self.overlay.setLookupTable(lut)
        self.overlay.setZValue(11)

    def clear(self):
        self.overlay.getViewBox().removeItem(self.indicator)
        self.overlay.getViewBox().removeItem(self.overlay)
        self.overlay.clear()


class BadDataOverlay:
    """
    Mixin class to be used with MIImageView and MIMiniImageView
    """
    def __init__(self):
        super().__init__()

        self.enabled_checks = OrderedDict()

        if hasattr(self, "sigTimeChanged"):
            self.sigTimeChanged.connect(self.check_for_bad_data)

    @property
    def image_item(self) -> ImageItem:
        raise NotImplementedError

    @property
    def viewbox(self) -> ViewBox:
        raise NotImplementedError

    def enable_nan_check(self, enable: bool = True):
        if enable:
            self.enable_check("nan", OVERLAY_COLOUR_NAN, 0, np.isnan)
        else:
            self.disable_check("nan")

    def enable_nonpositive_check(self, enable: bool = True):
        if enable:

            def is_non_positive(data):
                return data <= 0

            self.enable_check("nonpos", OVERLAY_COLOUR_NONPOSITVE, 1, is_non_positive)
        else:
            self.disable_check("nonpos")

    def enable_check(self, name: str, color: List[int], pos: int, func: Callable):
        if name not in self.enabled_checks:
            nan_icon_path = finder.ROOT_PATH + "/gui/ui/images/exclamation-triangle-red.png"
            nan_indicator = IndicatorIconView(self.viewbox, nan_icon_path, pos, color)
            nan_overlay = ImageItem()
            self.viewbox.addItem(nan_overlay)

            check = BadDataCheck(func, nan_indicator, nan_overlay, color)
            self.enabled_checks[name] = check
            self.check_for_bad_data()

    def disable_check(self, name: str):
        if name in self.enabled_checks:
            self.enabled_checks[name].clear()
            self.enabled_checks.pop(name, None)

    def _get_current_slice(self) -> Optional[np.ndarray]:
        data = self.image_item.image
        return data

    def check_for_bad_data(self):
        current_slice = self._get_current_slice()
        if current_slice is not None:
            for test in self.enabled_checks.values():
                test.do_check(current_slice)
