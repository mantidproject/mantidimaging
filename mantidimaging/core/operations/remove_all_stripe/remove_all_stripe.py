# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Any, TYPE_CHECKING

from algotom.prep.removal import remove_all_stripe

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from numpy import ndarray
    from mantidimaging.core.data.imagestack import ImageStack
    from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox


class RemoveAllStripesFilter(BaseFilter):
    """Stripe and ring artifact removal. Remove all types of stripe artifacts by
    combining algorithm 6, 5, and 3  in Vo et al., Optics Express 28396 (2018).

    Source: https://github.com/algotom/algotom

    Intended to be used on: Sinograms

    When: If stripes artifacts are present that have not been
    removed with outliers + flat-fielding the projections

    Caution: Horizontal stripes caused by changes in image intensity (pixel values)
    should be fixed by ROI Normalisation instead!
    """
    filter_name = "Remove all stripes"
    link_histograms = True
    operate_on_sinograms = True

    @staticmethod
    def filter_func(images: ImageStack, snr=3, la_size=61, sm_size=21, dim=1, progress=None):
        """
        :param snr: The ratio used to segment between useful information and
                    noise. Greater is less sensitive.
        :param la_size: The window size of the median filter to remove large
                        stripes.
        :param sm_size: The window size of the median filter to remove
                        small-to-medium stripes.
        :param dim: Whether to perform the median on 1D or 2D view of the data.

        :return: Remove all types of stripe artifacts.
        """
        if images.num_projections < 2:
            return images
        params = {"snr": snr, "la_size": la_size, "sm_size": sm_size, "dim": dim}
        if images.is_sinograms:
            compute_func = RemoveAllStripesFilter.compute_function_sino
        else:
            compute_func = RemoveAllStripesFilter.compute_function

        ps.run_compute_func(compute_func, images.num_sinograms, images.shared_array, params, progress)
        return images

    @staticmethod
    def compute_function_sino(index: int, array: ndarray, params: dict[str, Any]):
        array[index] = remove_all_stripe(array[index], **params)

    @staticmethod
    def compute_function(index: int, array: ndarray, params: dict[str, Any]):
        array[:, index, :] = remove_all_stripe(array[:, index, :], **params)

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        label, _ = add_property_to_form(BaseFilter.SINOGRAM_FILTER_INFO, Type.LABEL, form=form, on_change=on_change)
        # defaults taken from TomoPy integration
        # https://tomopy.readthedocs.io/en/latest/api/tomopy.prep.stripe.html#tomopy.prep.stripe.remove_all_stripe
        _, snr = add_property_to_form('Stripe ratio',
                                      Type.FLOAT,
                                      default_value=3,
                                      form=form,
                                      on_change=on_change,
                                      tooltip="Ratio used to segment between useful information and noise. "
                                      "Greater is less sensitive.")

        _, la_size = add_property_to_form('Large stripe kernel',
                                          Type.INT,
                                          default_value=21,
                                          valid_values=(1, 100),
                                          form=form,
                                          on_change=on_change,
                                          tooltip="Window size of the median filter to remove large stripes.")

        _, sm_size = add_property_to_form('Small stripe kernel',
                                          Type.INT,
                                          default_value=7,
                                          valid_values=(1, 100),
                                          form=form,
                                          on_change=on_change,
                                          tooltip="Window size of the median filter to remove small-to-medium stripes.")

        _, dim = add_property_to_form('Dimension of the window',
                                      Type.INT,
                                      default_value=2,
                                      valid_values=(1, 2),
                                      form=form,
                                      on_change=on_change,
                                      tooltip="Whether to perform the median on 1D or 2D view of the data")

        return {'snr': snr, 'la_size': la_size, 'sm_size': sm_size, 'dim': dim}

    @staticmethod
    def execute_wrapper(snr: QDoubleSpinBox, la_size: QSpinBox, sm_size: QSpinBox, dim: QSpinBox):  # type: ignore
        return partial(RemoveAllStripesFilter.filter_func,
                       snr=snr.value(),
                       la_size=la_size.value(),
                       sm_size=sm_size.value(),
                       dim=dim.value())

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Advanced
