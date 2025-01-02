# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Any, TYPE_CHECKING

from algotom.prep.removal import remove_stripe_based_fitting

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from numpy import ndarray
    from mantidimaging.core.data.imagestack import ImageStack
    from PyQt5.QtWidgets import QSpinBox


class RemoveStripeSortingFittingFilter(BaseFilter):
    """Stripe and ring artifact removal. Combination of algorithm 3 and 1 in Vo et al.,
    Optics Express 28396 (2018). Remove stripes using the sorting and fitting technique.

    Source: https://github.com/algotom/algotom

    Intended to be used on: Sinograms

    When: If stripes artifacts are present that have not been
    removed with outliers + flat-fielding the projections

    Caution: Horizontal stripes caused by changes in image intensity (pixel values)
    should be fixed by ROI Normalisation instead!
    """
    filter_name = "Remove stripes with sorting and fitting"
    link_histograms = True
    operate_on_sinograms = True

    @staticmethod
    def filter_func(images: ImageStack, order=1, sigma=3, progress=None):
        """
        :param order: The polynomial fit order. Check algotom docs for more
                      information.
        :param sigma: The sigma of the Gaussian window in the x-direction.

        :return: The ImageStack object with the stripes removed using the
                 sorting and fitting technique.
        """
        if images.num_projections < 2:
            return images
        params = {'order': order, 'sigma': sigma, 'sort': True}
        if images.is_sinograms:
            compute_func = RemoveStripeSortingFittingFilter.compute_function_sino
        else:
            compute_func = RemoveStripeSortingFittingFilter.compute_function
        ps.run_compute_func(compute_func, images.num_sinograms, images.shared_array, params, progress)

        return images

    @staticmethod
    def compute_function_sino(index: int, array: ndarray, params: dict[str, Any]):
        array[index] = remove_stripe_based_fitting(array[index], **params)

    @staticmethod
    def compute_function(index: int, array: ndarray, params: dict[str, Any]):
        array[:, index, :] = remove_stripe_based_fitting(array[:, index, :], **params)

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        label, _ = add_property_to_form(BaseFilter.SINOGRAM_FILTER_INFO, Type.LABEL, form=form, on_change=on_change)
        _, order = add_property_to_form('Polynomial fit order',
                                        Type.INT,
                                        default_value=1,
                                        form=form,
                                        on_change=on_change,
                                        tooltip="Polynomial fit order. Check algotom docs for more information")
        _, sigma = add_property_to_form('Sigma',
                                        Type.INT,
                                        default_value=3,
                                        form=form,
                                        on_change=on_change,
                                        tooltip="Sigma of the Gaussian window in the x-direction")

        return {'order': order, 'sigma': sigma}

    @staticmethod
    def execute_wrapper(order: QSpinBox, sigma: QSpinBox):  # type: ignore
        return partial(RemoveStripeSortingFittingFilter.filter_func, order=order.value(), sigma=sigma.value())

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Advanced
