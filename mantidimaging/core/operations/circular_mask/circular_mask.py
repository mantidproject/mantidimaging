# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial

from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.tools import importer
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility.qt_helpers import Type


class CircularMaskFilter(BaseFilter):
    """Masks a circular area around the center of the image, by setting it to a
    specified value.

    Intended to be used on: Reconstructed slices

    When: To remove reconstruction artifacts on the outer edge of the image.

    Caution: Ensure that the radius does not mask data from the sample.
    """
    filter_name = "Circular Mask"
    link_histograms = True

    @staticmethod
    def filter_func(data: Images,
                    circular_mask_ratio=0.95,
                    circular_mask_value=0.,
                    cores=None,
                    progress=None) -> Images:
        """
        :param data: Input data as a 3D numpy.ndarray
        :param circular_mask_ratio: The ratio to the full image.
                                    The ratio must be 0 < ratio < 1
        :param circular_mask_value: The value that all pixels in the mask
                                    will be set to.

        :return: The processed 3D numpy.ndarray
        """
        progress = Progress.ensure_instance(progress, num_steps=1, task_name='Circular Mask')

        if not circular_mask_ratio or not circular_mask_ratio < 1:
            raise ValueError(f'circular_mask_ratio must be > 0 and < 1. Value provided was {circular_mask_ratio}')

        tomopy = importer.do_importing('tomopy')

        with progress:
            progress.update(msg="Applying circular mask")

            # for some reason this doesn't like the ncore param, even though
            # it's in the official tomopy docs
            tomopy.circ_mask(arr=data.data, axis=0, ratio=circular_mask_ratio, val=circular_mask_value, ncore=cores)

        return data

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        _, radius_field = add_property_to_form('Radius',
                                               Type.FLOAT,
                                               0.95, (0.01, 0.99),
                                               form=form,
                                               on_change=on_change,
                                               tooltip="Radius [0, 1] of image that should be left untouched.")

        _, value_field = add_property_to_form('Set to value',
                                              Type.FLOAT,
                                              0, (-10000, 10000),
                                              form=form,
                                              on_change=on_change,
                                              tooltip="The value of the mask.")

        return {'radius_field': radius_field, 'value_field': value_field}

    @staticmethod
    def execute_wrapper(radius_field=None, value_field=None):
        return partial(CircularMaskFilter.filter_func,
                       circular_mask_ratio=radius_field.value(),
                       circular_mask_value=value_field.value())
