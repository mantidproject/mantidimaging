# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from typing import TYPE_CHECKING, List, Dict, Any

from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox
from algotom.prep.removal import remove_large_stripe

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.utility.qt_helpers import Type

if TYPE_CHECKING:
    from mantidimaging.core.data.imagestack import ImageStack
    from numpy import ndarray


class RemoveLargeStripesFilter(BaseFilter):
    """Stripe and ring artifact removal: Algorithm 5 in Vo et al., Optics Express 28396 (2018).
    Remove large stripes by: locating stripes, normalizing them to remove full stripes, using
    the sorting technique to remove partial stripes.

    Source: https://github.com/algotom/algotom

    Intended to be used on: Sinograms
    When: If stripes artifacts are present that have not been
    removed with outliers + flat-fielding the projections

    Caution: Horizontal stripes caused by changes in image intensity (pixel values)
    should be fixed by ROI Normalisation instead!
    """
    filter_name = "Remove large stripes"
    link_histograms = True
    operate_on_sinograms = True

    @classmethod
    def filter_func(cls, images: 'ImageStack', snr=3, la_size=61, progress=None):
        """
        :param snr: The ratio value.
        :param size: The window size of the median filter to remove large stripes.

        :return: The ImageStack object with large stripes removed.
        """
        params = {"snr": snr, "size": la_size}
        if images.is_sinograms:
            compute_func = cls.compute_function_sino
        else:
            compute_func = cls.compute_function
        ps.run_compute_func(compute_func, images.num_sinograms, [images.shared_array], params, progress)
        return images

    @staticmethod
    def compute_function_sino(index: int, arrays: List['ndarray'], params: Dict[str, Any]):
        arrays[0][index] = remove_large_stripe(arrays[0][index], **params)

    @staticmethod
    def compute_function(index: int, arrays: List['ndarray'], params: Dict[str, Any]):
        arrays[0][:, index, :] = remove_large_stripe(arrays[0][:, index, :], **params)

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form
        label, _ = add_property_to_form("This filter requires sinograms\nto produce a sensible result.",
                                        Type.LABEL,
                                        form=form,
                                        on_change=on_change)

        # defaults taken from TomoPy integration
        # https://tomopy.readthedocs.io/en/latest/api/tomopy.prep.stripe.html#tomopy.prep.stripe.remove_all_stripe
        _, snr = add_property_to_form('Stripe ratio',
                                      Type.FLOAT,
                                      default_value=3,
                                      form=form,
                                      on_change=on_change,
                                      tooltip="Ratio used to segment between useful information and noise"
                                      ". Greater is less sensitive.")

        _, la_size = add_property_to_form('Large stripe kernel',
                                          Type.INT,
                                          default_value=61,
                                          valid_values=(1, 100),
                                          form=form,
                                          on_change=on_change,
                                          tooltip="Window size of the median filter to remove large stripes.")

        return {'snr': snr, 'la_size': la_size}

    @staticmethod
    def execute_wrapper(snr: QDoubleSpinBox, la_size: QSpinBox):  # type: ignore
        return partial(RemoveLargeStripesFilter.filter_func, snr=snr.value(), la_size=la_size.value())

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Advanced
