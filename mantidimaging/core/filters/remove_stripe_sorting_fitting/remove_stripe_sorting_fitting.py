from functools import partial

from PyQt5.QtWidgets import QSpinBox
from sarepy.prep.stripe_removal_improved import remove_stripe_based_sorting_fitting

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.gui.utility.qt_helpers import Type


class RemoveStripeSortingFittingFilter(BaseFilter):
    filter_name = "Remove stripes with sorting and fitting"

    @staticmethod
    def filter_func(images, order=1, sigmax=3, sigmay=3, cores=None, chunksize=None, progress=None):
        f = psm.create_partial(remove_stripe_based_sorting_fitting,
                               psm.return_fwd_func,
                               order=order,
                               sigmax=sigmax,
                               sigmay=sigmay)

        psm.execute(images.data, f, cores, chunksize, progress)
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
                                        on_change=on_change)
        _, sigmax = add_property_to_form('Sigma X',
                                         Type.INT,
                                         default_value=3,
                                         form=form,
                                         on_change=on_change,
                                         tooltip="Sigma of the Gaussian window in the x-direction")
        _, sigmay = add_property_to_form('Sigma Y',
                                         Type.INT,
                                         default_value=3,
                                         form=form,
                                         on_change=on_change,
                                         tooltip="Sigma of the Gaussian window in the y-direction")

        return {'order': order, 'sigmax': sigmax, 'sigmay': sigmay}

    @staticmethod
    def execute_wrapper(order: QSpinBox, sigmax: QSpinBox, sigmay: QSpinBox):  # type: ignore
        return partial(RemoveStripeSortingFittingFilter.filter_func,
                       order=order.value(),
                       sigmax=sigmax.value(),
                       sigmay=sigmay.value())
