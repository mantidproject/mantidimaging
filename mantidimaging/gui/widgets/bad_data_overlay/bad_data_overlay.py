# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from collections import OrderedDict
from typing import Callable

import numpy as np
from pyqtgraph import ImageItem, ViewBox

from mantidimaging.gui.widgets.indicator_icon.view import IndicatorIconView
from mantidimaging.core.utility import finder


class BadDataCheck:
    check_function: Callable[[np.ndarray], np.ndarray]
    indicator: IndicatorIconView

    def __init__(self, check_function, indicator):
        self.check_function = check_function
        self.indicator = indicator

    def do_check(self, data):
        bad_data = self.check_function(data)
        any_bad = bad_data.any()
        # cast any_bad to python bool to prevent DeprecationWarning
        self.indicator.setVisible(bool(any_bad))


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
            nan_icon_path = finder.ROOT_PATH + "/gui/ui/images/exclamation-triangle-red.png"
            nan_indicator = IndicatorIconView(self.viewbox, nan_icon_path, 0)
            test = BadDataCheck(np.isnan, nan_indicator)
            self.enabled_checks["nan"] = test
        else:
            self.enabled_checks.pop("nan", None)

    def _get_current_slice(self) -> np.ndarray:
        data = self.image_item.image
        return data

    def check_for_bad_data(self):
        current_slice = self._get_current_slice()
        for test in self.enabled_checks.values():
            test.do_check(current_slice)
