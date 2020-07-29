from functools import partial

from PyQt5.QtWidgets import QSpinBox
from sarepy.prep.stripe_removal_improved import remove_stripe_based_filtering_sorting, \
    remove_stripe_based_2d_filtering_sorting

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.gui.utility.qt_helpers import Type


class RemoveStripeFilteringFilter(BaseFilter):
    filter_name = "Remove stripes with filtering"

    @staticmethod
    def filter_func(images, sigma=3, size=21, window_dim=1, filtering_dim=1, cores=None, chunksize=None, progress=None):
        if filtering_dim == 1:
            f = psm.create_partial(remove_stripe_based_filtering_sorting, psm.return_fwd_func,
                                   sigma=sigma, size=size, dim=window_dim)
        else:
            f = psm.create_partial(remove_stripe_based_2d_filtering_sorting, psm.return_fwd_func,
                                   sigma=sigma, size=size, dim=window_dim)
        psm.execute(images.sinograms, f, cores, chunksize, progress)
        return images

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        _, sigma = add_property_to_form('Sigma', Type.INT, default_value=3, form=form, on_change=on_change,
                                        tooltip="Sigma of the Gaussian window used to separate the low-pass and"
                                                " high-pass components of the intensity profile of each column.")

        _, size = add_property_to_form('Stripe kernel', Type.INT, default_value=21, form=form,
                                       on_change=on_change,
                                       tooltip="Window size of the median filter to remove large stripes.")

        _, window_dim = add_property_to_form('Dimension of the window', Type.INT, default_value=1, valid_values=(1, 2),
                                             form=form, on_change=on_change)

        _, filtering_dim = add_property_to_form('Filtering dim', Type.INT, default_value=1, valid_values=(1, 2),
                                                form=form, on_change=on_change,
                                                tooltip="Whether to use a 1D or 2D low-pass filter. "
                                                        "This uses different Sarepy methods")
        return {'sigma': sigma,
                'size': size,
                'window_dim': window_dim,
                'filtering_dim': filtering_dim}

    @staticmethod
    def execute_wrapper(sigma: QSpinBox, size: QSpinBox, window_dim: QSpinBox, filtering_dim: QSpinBox):
        return partial(RemoveStripeFilteringFilter.filter_func, sigma=sigma.value(), size=size.value(),
                       window_dim=window_dim.value(), filtering_dim=filtering_dim.value())
