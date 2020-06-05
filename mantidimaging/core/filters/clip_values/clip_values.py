from functools import partial

from mantidimaging.core.data import Images

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.utility.progress_reporting import Progress


class ClipValuesFilter(BaseFilter):
    filter_name = "Clip Values"

    @staticmethod
    def filter_func(data,
                    clip_min=None,
                    clip_max=None,
                    clip_min_new_value=None,
                    clip_max_new_value=None,
                    progress=None) -> Images:
        """
        Clip values below the min and above the max pixels.

        :param data: Input data as a 3D numpy.ndarray.
        :param clip_min: The minimum value to be clipped from the data.
                         If None is provided then no lower threshold is used.
        :param clip_max: The maximum value to be clipped from the data.
                         If None is provided then no upper threshold is used.

        :param clip_min_new_value: The value to use when replacing values less than
                                   clip_min.
                                   If None is provided then the value of clip_min
                                   is used.

        :param clip_max_new_value: The value to use when replacing values greater
                                   than clip_max.
                                   If None is provided then the value of clip_max
                                   is used.

        :return: The processed 3D numpy.ndarray.
        """
        progress = Progress.ensure_instance(progress, num_steps=2, task_name='Clipping Values.')

        # we're using is not None because if the value specified is 0.0 that
        # evaluates to false
        if clip_min is not None or clip_max is not None:
            with progress:
                sample = data.sample
                progress.update(msg="Determining clip min and clip max")
                clip_min = clip_min if clip_min is not None else sample.min()
                clip_max = clip_max if clip_max is not None else sample.max()

                clip_min_new_value = clip_min_new_value if clip_min_new_value is not None else clip_min

                clip_max_new_value = clip_max_new_value if clip_max_new_value is not None else clip_max

                progress.update(msg=f"Clipping data with values min {clip_min} and max {clip_max}.")

                # this is the fastest way to clip the values, np.clip does not do
                # the clipping in place and ends up copying the data
                sample[sample < clip_min] = clip_min_new_value
                sample[sample > clip_max] = clip_max_new_value

        return data

    @staticmethod
    def register_gui(form, on_change):
        from mantidimaging.gui.utility import add_property_to_form

        value_range = (-10000000, 10000000)

        _, clip_min_field = add_property_to_form('Clip Min',
                                                 'float',
                                                 valid_values=value_range,
                                                 form=form,
                                                 on_change=on_change)
        clip_min_field.setDecimals(7)

        _, clip_max_field = add_property_to_form('Clip Max',
                                                 'float',
                                                 valid_values=value_range,
                                                 form=form,
                                                 on_change=on_change)
        clip_max_field.setDecimals(7)

        _, clip_min_new_value_field = add_property_to_form(
            'Min Replacement Value',
            'float',
            valid_values=value_range,
            form=form,
            on_change=on_change,
            tooltip='The value that will be used to replace pixel values '
                    'that fall below Clip Min.')

        _, clip_max_new_value_field = add_property_to_form(
            'Max Replacement Value',
            'float',
            valid_values=value_range,
            form=form,
            on_change=on_change,
            tooltip='The value that will be used to replace pixel values '
                    'that are above Clip Max.')

        clip_min_new_value_field.setDecimals(7)
        clip_max_new_value_field.setDecimals(7)

        # Ensures that the new_value fields are set to be clip_min
        # or clip_max, unless the user has explicitly changed them
        def update_field_on_value_changed(field, field_new_value):
            field_new_value.setValue(field.value())

        # using lambda we can pass in parameters
        clip_min_field.valueChanged.connect(
            lambda: update_field_on_value_changed(clip_min_field, clip_min_new_value_field))
        clip_max_field.valueChanged.connect(
            lambda: update_field_on_value_changed(clip_max_field, clip_max_new_value_field))

        return {
            "clip_min_field": clip_min_field,
            "clip_max_field": clip_max_field,
            "clip_min_new_value_field": clip_min_new_value_field,
            "clip_max_new_value_field": clip_max_new_value_field
        }

    @staticmethod
    def execute_wrapper(clip_min_field=None,
                        clip_max_field=None,
                        clip_min_new_value_field=None,
                        clip_max_new_value_field=None):
        clip_min = clip_min_field.value()
        clip_max = clip_max_field.value()
        clip_min_new_value = clip_min_new_value_field.value()
        clip_max_new_value = clip_max_new_value_field.value()
        return partial(ClipValuesFilter.filter_func,
                       clip_min=clip_min,
                       clip_max=clip_max,
                       clip_min_new_value=clip_min_new_value,
                       clip_max_new_value=clip_max_new_value)
