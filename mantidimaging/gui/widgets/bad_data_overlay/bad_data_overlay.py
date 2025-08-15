# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import abstractmethod, ABC
from collections.abc import Callable

import numpy as np
from pyqtgraph import ColorMap, ImageItem, ViewBox

from mantidimaging.gui.utility.qt_helpers import _metaclass_sip_abc
from mantidimaging.gui.widgets.indicator_icon.view import IndicatorIconView
from mantidimaging.core.utility import finder

OVERLAY_COLOUR_NAN = [200, 0, 200, 255]
OVERLAY_COLOUR_ZERO = [255, 140, 0, 255]
OVERLAY_COLOUR_NEGATIVE = [0, 180, 0, 255]
OVERLAY_COLOUR_MESSAGE = [0, 120, 255, 255]


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

    def do_check(self, data) -> None:
        bad_data = self.check_function(data)
        any_bad = bad_data.any()
        # cast any_bad to python bool to prevent DeprecationWarning
        self.indicator.setVisible(bool(any_bad))

        self.overlay.setImage(bad_data, autoLevels=False)

    def setup_overlay(self) -> None:
        color = np.array([[0, 0, 0, 0], self.color], dtype=np.ubyte)
        color_map = ColorMap([0, 1], color)
        self.overlay.setVisible(False)
        lut = color_map.getLookupTable(0, 1, 2)
        self.overlay.setLookupTable(lut)
        self.overlay.setZValue(11)
        self.overlay.setLevels([0, 1])

    def remove(self) -> None:
        self.overlay.getViewBox().removeItem(self.indicator)
        self.overlay.getViewBox().removeItem(self.overlay)
        self.overlay.clear()

    def clear(self) -> None:
        self.indicator.setVisible(False)
        self.overlay.clear()


class BadDataOverlay(ABC, metaclass=_metaclass_sip_abc):
    """
    Mixin class to be used with MIImageView and MIMiniImageView
    """

    def __init__(self) -> None:
        super().__init__()

        self.enabled_checks: dict[str, BadDataCheck] = {}
        self.message_indicator: IndicatorIconView | None = None

        if hasattr(self, "sigTimeChanged"):
            self.sigTimeChanged.connect(self.check_for_bad_data)

    @property
    @abstractmethod
    def image_item(self) -> ImageItem:
        ...

    @property
    @abstractmethod
    def viewbox(self) -> ViewBox:
        ...

    def enable_nan_check(self, enable: bool = True, actions: list[tuple[str, Callable]] | None = None) -> None:
        if enable:
            self.enable_check("nan", OVERLAY_COLOUR_NAN, 0, np.isnan, "Invalid values: Not a number", actions)
        else:
            self.disable_check("nan")

    def enable_value_check(self, enable: bool = True, actions: list[tuple[str, Callable]] | None = None) -> None:
        if enable:

            def is_zero(data):
                data = np.asarray(data, dtype=float)
                return (data == 0) & ~np.isnan(data)

            def is_negative(data):
                data = np.asarray(data, dtype=float)
                return (data < 0) & ~np.isnan(data)

            def is_nan(data):
                data = np.asarray(data, dtype=float)
                return np.isnan(data)

            self.enable_check("zero", OVERLAY_COLOUR_ZERO, 1, is_zero, "Zero values", actions)
            self.enable_check("negative", OVERLAY_COLOUR_NEGATIVE, 2, is_negative, "Negative values", actions)
            self.enable_check("nan", OVERLAY_COLOUR_NAN, 3, is_nan, "Invalid values: Not a number", actions)
        else:
            self.disable_check("zero")
            self.disable_check("negative")
            self.disable_check("nan")

    def enable_check(self, name: str, color: list[int], pos: int, func: Callable, message: str,
                     actions: list[tuple[str, Callable]] | None) -> None:
        if name not in self.enabled_checks:
            icon_path = (finder.ROOT_PATH / "gui" / "ui" / "images" / "exclamation-triangle-red.png").as_posix()
            indicator = IndicatorIconView(self.viewbox, icon_path, pos, color, message)
            if actions is not None:
                indicator.add_actions(actions)
            overlay = ImageItem()
            self.viewbox.addItem(overlay)

            check = BadDataCheck(func, indicator, overlay, color)
            self.enabled_checks[name] = check
            self.check_for_bad_data()

    def disable_check(self, name: str) -> None:
        if name in self.enabled_checks:
            self.enabled_checks[name].remove()
            self.enabled_checks.pop(name, None)

    def _get_current_slice(self) -> np.ndarray | None:
        data = self.image_item.image
        return data

    def check_for_bad_data(self) -> None:
        current_slice = self._get_current_slice()
        if current_slice is not None:
            for test in self.enabled_checks.values():
                test.do_check(current_slice)

    def clear_overlays(self) -> None:
        for check in self.enabled_checks.values():
            check.clear()

    def enable_message(self, enable: bool = True) -> None:
        if enable:
            icon_path = (finder.ROOT_PATH / "gui" / "ui" / "images" / "exclamation-triangle-red.png").as_posix()
            self.message_indicator = IndicatorIconView(self.viewbox, icon_path, 0, OVERLAY_COLOUR_MESSAGE, "")
            self.message_indicator.setVisible(False)
        else:
            self.message_indicator = None

    def show_message(self, message: str | None) -> None:
        if self.message_indicator is None:
            return
        if message:
            self.message_indicator.set_message(message)
            self.message_indicator.setVisible(True)
        else:
            self.message_indicator.setVisible(False)
