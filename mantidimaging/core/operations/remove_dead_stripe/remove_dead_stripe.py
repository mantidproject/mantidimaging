# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from mantidimaging.core.data.imagestack import ImageStack

from PyQt5.QtWidgets import QDoubleSpinBox, QSpinBox
from algotom.prep.removal import remove_dead_stripe

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.utility.qt_helpers import Type


class RemoveDeadStripesFilter(BaseFilter):
    """Stripe and ring artifact removal. Algorithm 6 in Vo et al., Optics Express 28396 (2018).
    Remove unresponsive or fluctuating stripes by: locating stripes, correction by interpolation.

    Source: https://github.com/algotom/algotom

    Intended to be used on: Sinograms

    When: If stripes artifacts are present that have not been
    removed with outliers + flat-fielding the projections

    Caution: Horizontal stripes caused by changes in image intensity (pixel values)
    should be fixed by ROI Normalisation instead!
    """
    filter_name = "Remove dead stripes"
    link_histograms = True

    @staticmethod
    def filter_func(images: ImageStack, snr=3, size=61, cores=None, chunksize=None, progress=None):
        f = ps.create_partial(remove_dead_stripe, ps.return_to_self, snr=snr, size=size, residual=False)
        ps.execute(f, [images.shared_array], images.data.shape[0], progress, cores=cores)
        return images

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

        _, size = add_property_to_form('Stripe kernel',
                                       Type.INT,
                                       default_value=21,
                                       valid_values=(1, 100),
                                       form=form,
                                       on_change=on_change,
                                       tooltip="Window size of the median filter to remove large stripes.")

        return {'snr': snr, 'size': size}

    @staticmethod
    def execute_wrapper(snr: QDoubleSpinBox, size: QSpinBox):  # type: ignore
        return partial(RemoveDeadStripesFilter.filter_func, snr=snr.value(), size=size.value())

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Advanced
