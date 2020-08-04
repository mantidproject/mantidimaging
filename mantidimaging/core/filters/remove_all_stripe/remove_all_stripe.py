from functools import partial

from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox
from sarepy.prep.stripe_removal_original import remove_all_stripe

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.gui.utility.qt_helpers import Type


class RemoveAllStripesFilter(BaseFilter):
    filter_name = "Remove all stripes"

    @staticmethod
    def filter_func(images, snr=3, la_size=61, sm_size=21, dim=1, cores=None, chunksize=None, progress=None):
        f = psm.create_partial(remove_all_stripe,
                               psm.return_fwd_func,
                               snr=snr,
                               la_size=la_size,
                               sm_size=sm_size,
                               dim=dim)
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
                                      tooltip="Ratio used to segment between useful information and noise. "
                                      "Greater is less sensitive.")

        _, la_size = add_property_to_form('Large stripe kernel',
                                          Type.INT,
                                          default_value=61,
                                          valid_values=(1, 100),
                                          form=form,
                                          on_change=on_change,
                                          tooltip="Window size of the median filter to remove large stripes.")

        _, sm_size = add_property_to_form('Small stripe kernel',
                                          Type.INT,
                                          default_value=21,
                                          valid_values=(1, 100),
                                          form=form,
                                          on_change=on_change,
                                          tooltip="Window size of the median filter to remove small-to-medium stripes.")

        _, dim = add_property_to_form('Dimension of the window',
                                      Type.INT,
                                      default_value=1,
                                      valid_values=(1, 2),
                                      form=form,
                                      on_change=on_change)
        return {'snr': snr, 'la_size': la_size, 'sm_size': sm_size, 'dim': dim}

    @staticmethod
    def execute_wrapper(snr: QDoubleSpinBox, la_size: QSpinBox, sm_size: QSpinBox, dim: QSpinBox):
        return partial(RemoveAllStripesFilter.filter_func,
                       snr=snr.value(),
                       la_size=la_size.value(),
                       sm_size=sm_size.value(),
                       dim=dim.value())
