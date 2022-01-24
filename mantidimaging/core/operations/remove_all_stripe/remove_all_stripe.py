# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from mantidimaging.core.data.images import Images

from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox
from algotom.prep.removal import remove_all_stripe

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.utility.qt_helpers import Type


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

    @staticmethod
    def filter_func(images: Images, snr=3, la_size=61, sm_size=21, dim=1, cores=None, chunksize=None, progress=None):
        f = ps.create_partial(remove_all_stripe, ps.return_to_self, snr=snr, la_size=la_size, sm_size=sm_size, dim=dim)
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
