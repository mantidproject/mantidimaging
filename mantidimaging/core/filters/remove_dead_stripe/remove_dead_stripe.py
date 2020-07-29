from functools import partial

from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox
from sarepy.prep.stripe_removal_original import remove_unresponsive_and_fluctuating_stripe

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.gui.utility.qt_helpers import Type


class RemoveDeadStripesFilter(BaseFilter):
    filter_name = "Remove dead stripes"

    @staticmethod
    def filter_func(images, snr=3, size=61, cores=None, chunksize=None, progress=None):
        f = psm.create_partial(remove_unresponsive_and_fluctuating_stripe, psm.return_fwd_func, snr=snr, size=size)
        psm.execute(images.sinograms(), f, cores, chunksize, progress)
        return images

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        # defaults taken from TomoPy integration
        # https://tomopy.readthedocs.io/en/latest/api/tomopy.prep.stripe.html#tomopy.prep.stripe.remove_all_stripe
        _, snr = add_property_to_form('Stripe ratio', Type.FLOAT, default_value=3, form=form, on_change=on_change,
                                      tooltip="Ratio used to segment between useful information and noise"
                                              ". Greater is less sensitive.")

        _, size = add_property_to_form('Stripe kernel', Type.INT, default_value=21, form=form,
                                          on_change=on_change,
                                          tooltip="Window size of the median filter to remove large stripes.")

        return {'snr': snr,
                'size': size}

    @staticmethod
    def execute_wrapper(snr: QDoubleSpinBox, size: QSpinBox):
        return partial(RemoveDeadStripesFilter.filter_func, snr=snr.value(), size=size.value())
