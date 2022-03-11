# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from mantidimaging.core.data.imagestack import ImageStack

from PyQt5.QtWidgets import QSpinBox
from algotom.prep.removal import remove_stripe_based_fitting

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.utility.qt_helpers import Type


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

    @staticmethod
    def filter_func(images: ImageStack, order=1, sigma=3, cores=None, chunksize=None, progress=None):
        f = ps.create_partial(remove_stripe_based_fitting, ps.return_to_self, order=order, sigma=sigma, sort=True)

        ps.shared_list = [images.data]
        ps.execute(f, images.data.shape[0], progress, cores=cores)
        return images

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        label, _ = add_property_to_form("This filter requires sinograms\nto produce a sensible result.",
                                        Type.LABEL,
                                        form=form,
                                        on_change=on_change)
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
