from functools import partial

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.tools import importer
from mantidimaging.core.utility.progress_reporting import Progress


class CircularMaskFilter(BaseFilter):
    filter_name = "Circular Mask"

    @staticmethod
    def filter_func(data, circular_mask_ratio, circular_mask_value=0., progress=None):
        """
        :param data: Input data as a 3D numpy.ndarray
        :param circular_mask_ratio: The ratio to the full image.
                                    The ratio must be 0 < ratio < 1
        :param circular_mask_value: The value that all pixels in the mask
                                    will be set to.

        :return: The processed 3D numpy.ndarray
        """
        progress = Progress.ensure_instance(progress, num_steps=1, task_name='Circular Mask')

        if circular_mask_ratio and 0 < circular_mask_ratio < 1:
            tomopy = importer.do_importing('tomopy')

            with progress:
                progress.update(msg="Applying circular mask.")

                # for some reason this doesn't like the ncore param, even though
                # it's in the official tomopy docs
                tomopy.circ_mask(arr=data.sample, axis=0, ratio=circular_mask_ratio, val=circular_mask_value)

        return data

    @staticmethod
    def register_gui(form, on_change):
        from mantidimaging.gui.utility import add_property_to_form

        _, radius_field = add_property_to_form('Radius', 'float', 0.95, (0.0, 1.0), form=form, on_change=on_change)

        _, value_field = add_property_to_form('Set to value',
                                              'float',
                                              0, (-10000, 10000),
                                              form=form,
                                              on_change=on_change)

        return {'radius_field': radius_field, 'value_field': value_field}

    @staticmethod
    def execute_wrapper(radius_field=None, value_field=None):
        return partial(CircularMaskFilter.filter_func,
                       circular_mask_ratio=radius_field.value(),
                       circular_mask_value=value_field.value())
