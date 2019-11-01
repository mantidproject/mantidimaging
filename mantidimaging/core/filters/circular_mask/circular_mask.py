from functools import partial

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.tools import importer
from mantidimaging.core.utility.progress_reporting import Progress


class CircularMaskFilter(BaseFilter):
    filter_name = "Circular Mask"
    
    def _filter_func(self, data, circular_mask_ratio=None, circular_mask_value=0.,
                     progress=None):
        """
        :param data: Input data as a 3D numpy.ndarray
        :param circular_mask_ratio: The ratio to the full image.
                                    The ratio must be 0 < ratio < 1
        :param circular_mask_value: The value that all pixels in the mask
                                    will be set to.

        :return: The processed 3D numpy.ndarray
        """
        progress = Progress.ensure_instance(progress, task_name='Circular Mask')

        if circular_mask_ratio and 0 < circular_mask_ratio < 1:
            tomopy = importer.do_importing('tomopy')

            with progress:
                progress.update(msg="Circular mask")

                # for some reason this doesn't like the ncore param, even though
                # it's in the official tomopy docs
                tomopy.circ_mask(
                    arr=data,
                    axis=0,
                    ratio=circular_mask_ratio,
                    val=circular_mask_value)

        return data

    def register_gui(self, form, on_change):
        from mantidimaging.gui.utility import add_property_to_form

        _, radius_field = add_property_to_form(
            'Radius', 'float', 0.95, (0.0, 1.0),
            form=form, on_change=on_change)

        _, value_field = add_property_to_form(
            'Set to value', 'float', 0, (-10000, 10000),
            form=form, on_change=on_change)

        return {
            'radius_field': radius_field,
            'value_field': value_field
        }

    def execute_wrapper(self, radius_field=None, value_field=None):
        return partial(self._filter_func,
                       circular_mask_ratio=radius_field.value(),
                       circular_mask_value=value_field.value())


def _cli_register(parser):
    parser.add_argument(
        "--circular-mask",
        required=False,
        type=float,
        default=None,
        help="Radius of the circular mask to apply on the "
             "reconstructed volume.\n"
             "It is given in range [0,1) relative to the size of the "
             "smaller dimension/edge "
             "of the slices.\nEmpty or zero implies no masking.")

    parser.add_argument(
        "--circular-mask-val",
        required=False,
        type=float,
        default=0.0,
        help="Default: %(default)s. "
             "The value that the pixels in the mask will be set to.")

    return parser
