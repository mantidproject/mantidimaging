# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from mantidimaging.core.data.images import Images

from PyQt5.QtWidgets import QSpinBox
from algotom.prep.removal import remove_stripe_based_filtering, remove_stripe_based_2d_filtering_sorting

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.utility.qt_helpers import Type


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

    @staticmethod
    def filter_func(images: Images,
                    sigma=3,
                    size=21,
                    window_dim=1,
                    filtering_dim=1,
                    cores=None,
                    chunksize=None,
                    progress=None):
        if filtering_dim == 1:
            f = ps.create_partial(remove_stripe_based_filtering,
                                  ps.return_to_self,
                                  sigma=sigma,
                                  size=size,
                                  dim=window_dim,
                                  sort=True)
        else:
            f = ps.create_partial(remove_stripe_based_2d_filtering_sorting,
                                  ps.return_to_self,
                                  sigma=sigma,
                                  size=size,
                                  dim=window_dim)
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
