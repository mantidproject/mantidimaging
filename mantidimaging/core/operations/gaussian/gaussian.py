# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Callable

from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    import numpy as np
    from mantidimaging.gui.mvp_base import BaseMainWindowView
    from mantidimaging.core.data import ImageStack
    from PyQt5.QtWidgets import QFormLayout, QWidget


class GaussianFilter(BaseFilter):
    filter_name = "Gaussian"
    link_histograms = True

    @classmethod
    def filter_func(cls, images: ImageStack, size: int, mode: str = 'reflect', order: int = 0, progress=None):
        if size <= 1:
            raise ValueError(f"Size parameter must be greater than 1, but value provided was {size}")

        params = {'size': size, 'mode': mode, 'order': order}
        ps.run_compute_func(cls.compute_function, images.data.shape[0], [images.shared_array], params, progress)

        return images

    @staticmethod
    def compute_function(i: int, arrays: List[np.ndarray], params: Dict[str, any]):
        from scipy.ndimage import gaussian_filter
        arrays[0][i] = gaussian_filter(arrays[0][i], sigma=params['size'], order=params['order'], mode=params['mode'])

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BaseMainWindowView') -> Dict[str, 'QWidget']:
        _, size_field = add_property_to_form('Kernel Size',
                                             Type.INT,
                                             3, (2, 1000),
                                             form=form,
                                             on_change=on_change,
                                             tooltip="Size of the median filter kernel")

        _, order_field = add_property_to_form('Order',
                                              Type.INT,
                                              0, (0, 3),
                                              form=form,
                                              on_change=on_change,
                                              tooltip="Order of the Gaussian filter")

        _, mode_field = add_property_to_form('Edge Mode',
                                             Type.CHOICE,
                                             valid_values=modes(),
                                             form=form,
                                             on_change=on_change,
                                             tooltip="Mode to handle the edges of the image")

        return {'size_field': size_field, 'order_field': order_field, 'mode_field': mode_field}

    @classmethod
    def execute_wrapper(cls, size_field=None, order_field=None, mode_field=None) -> Callable:

        def wrapper(images: ImageStack, progress=None):
            return cls.filter_func(images,
                                   size=size_field.value(),
                                   mode=mode_field.currentText(),
                                   order=order_field.value(),
                                   progress=progress)

        return wrapper


def modes():
    return ['reflect', 'constant', 'nearest', 'mirror', 'wrap']
