from functools import partial

from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox
from sarepy.prep.stripe_removal_original import remove_large_stripe

from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.gui.utility.qt_helpers import Type


class RemoveLargeStripesFilter(BaseFilter):
    """Algorithm 5 in the paper. Remove large stripes by: locating stripes,
    normalizing to remove full stripes, using the sorting technique to remove
    partial stripes. Angular direction is along the axis 0.

    Source: https://github.com/nghia-vo/sarepy

    Intended to be used on: Sinograms
    When: If stripes artifacts are present that have not been
    removed with outliers + flat-fielding the projections

    Caution: Horizontal stripes are caused by changes in image intensity (pixel values),
    and should be fixed by ROI Normalisation instead!
    """
    filter_name = "Remove large stripes"

    @staticmethod
    def filter_func(images, snr=3, la_size=61, cores=None, chunksize=None, progress=None):
        f = psm.create_partial(remove_large_stripe, psm.return_fwd_func, snr=snr, size=la_size)
        psm.execute(images.data, f, cores, chunksize, progress)
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
