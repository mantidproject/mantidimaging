# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Any, TYPE_CHECKING

from algotom.prep.removal import remove_stripe_based_filtering, remove_stripe_based_2d_filtering_sorting

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from numpy import ndarray
    from mantidimaging.core.data.imagestack import ImageStack
    from PyQt5.QtWidgets import QSpinBox


class RemoveStripeFilteringFilter(BaseFilter):
    """Stripe and ring artifact removal. Combination of algorithm 2 and algorithm 3 in Vo et al.,
    Optics Express 28396 (2018). Removing stripes using the filtering and sorting technique.

    Source: https://github.com/algotom/algotom

    Intended to be used on: Sinograms

    When: If stripes artifacts are present that have not been
    removed with outliers + flat-fielding the projections

    Caution: Horizontal stripes caused by changes in image intensity (pixel values)
    should be fixed by ROI Normalisation instead!
    """
    filter_name = "Remove stripes with filtering"
    link_histograms = True
    operate_on_sinograms = True

    @staticmethod
    def filter_func(images: ImageStack, sigma=3, size=21, window_dim=1, filtering_dim=1, progress=None):
        """
        :param sigma: The sigma of the Gaussian window used to separate the
                      low-pass and high-pass components of the intensity profile
                      of each column.
        :param size: The window size of the median filter to remove large
                     stripes.
        :param window_dim: Whether to perform the median on 1D or 2D view of the
                           data.
        :param filtering_dim: Whether to use a 1D or 2D low-pass filter. This
                              uses different Sarepy methods.

        :return: The ImageStack object with the stripes removed using the
                 filtering and sorting technique.
        """
        params = {"sigma": sigma, "size": size, "dim": window_dim}
        if images.is_sinograms:
            if filtering_dim == 1:
                params["sort"] = True
                compute_func = RemoveStripeFilteringFilter.compute_function_sino
            else:
                compute_func = RemoveStripeFilteringFilter.compute_function_2d_sino
        else:
            if filtering_dim == 1:
                params["sort"] = True
                compute_func = RemoveStripeFilteringFilter.compute_function
            else:
                compute_func = RemoveStripeFilteringFilter.compute_function_2d

        ps.run_compute_func(compute_func, images.num_sinograms, images.shared_array, params, progress)
        return images

    @staticmethod
    def compute_function_sino(index: int, array: ndarray, params: dict[str, Any]):
        array[index] = remove_stripe_based_filtering(array[index], **params)

    @staticmethod
    def compute_function(index: int, array: ndarray, params: dict[str, Any]):
        array[:, index, :] = remove_stripe_based_filtering(array[:, index, :], **params)

    @staticmethod
    def compute_function_2d_sino(index: int, array: ndarray, params: dict[str, Any]):
        array[index] = remove_stripe_based_2d_filtering_sorting(array[index], **params)

    @staticmethod
    def compute_function_2d(index: int, array: ndarray, params: dict[str, Any]):
        array[:, index, :] = remove_stripe_based_2d_filtering_sorting(array[:, index, :], **params)

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        label, _ = add_property_to_form(BaseFilter.SINOGRAM_FILTER_INFO, Type.LABEL, form=form, on_change=on_change)
        _, sigma = add_property_to_form('Sigma',
                                        Type.INT,
                                        default_value=3,
                                        form=form,
                                        on_change=on_change,
                                        tooltip="Sigma of the Gaussian window used to separate the low-pass and"
                                        " high-pass components of the intensity profile of each column.")

        _, size = add_property_to_form('Stripe kernel',
                                       Type.INT,
                                       default_value=21,
                                       form=form,
                                       on_change=on_change,
                                       tooltip="Window size of the median filter to remove large stripes.")

        _, window_dim = add_property_to_form('Dimension of the window',
                                             Type.INT,
                                             default_value=1,
                                             valid_values=(1, 2),
                                             form=form,
                                             on_change=on_change,
                                             tooltip="Whether to perform the median on 1D or 2D view of the data")

        _, filtering_dim = add_property_to_form('Filtering dim',
                                                Type.INT,
                                                default_value=1,
                                                valid_values=(1, 2),
                                                form=form,
                                                on_change=on_change,
                                                tooltip="Whether to use a 1D or 2D low-pass filter. "
                                                "This uses different Sarepy methods")
        return {'sigma': sigma, 'size': size, 'window_dim': window_dim, 'filtering_dim': filtering_dim}

    @staticmethod
    def execute_wrapper(sigma: QSpinBox, size: QSpinBox, window_dim: QSpinBox, filtering_dim: QSpinBox):  # type: ignore
        return partial(RemoveStripeFilteringFilter.filter_func,
                       sigma=sigma.value(),
                       size=size.value(),
                       window_dim=window_dim.value(),
                       filtering_dim=filtering_dim.value())

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Advanced
