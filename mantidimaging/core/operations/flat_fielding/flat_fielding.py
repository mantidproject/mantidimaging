from functools import partial
from typing import Any, Dict

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import two_shared_mem as ptsm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.widgets.stack_selector import StackSelectorWidgetView
from mantidimaging.gui.windows.operations import FiltersWindowView

# The smallest and largest allowed pixel value
MINIMUM_PIXEL_VALUE = 1e-9
MAXIMUM_PIXEL_VALUE = 1e9


class FlatFieldFilter(BaseFilter):
    """Uses the flat (open beam) and dark images to reduce the noise in the
    projection images.

    Intended to be used on: Projections

    When: As one of the first pre-processing steps to greatly reduce noise in the data

    Caution: Make sure the correct stacks are selected for flat and dark.

    Caution: Check that the flat and dark images don't have any very bright pixels,
    or this will introduce additional noise in the sample.
    """
    filter_name = 'Flat-fielding'

    @staticmethod
    def filter_func(data: Images,
                    flat_before: Images = None,
                    flat_after: Images = None,
                    dark_before: Images = None,
                    dark_after: Images = None,
                    selected_flat_fielding: str = None,
                    cores=None,
                    chunksize=None,
                    progress=None) -> Images:
        """Do background correction with flat and dark images.

        :param data: Sample data which is to be processed. Expected in radiograms
        :param flat_before: Flat (open beam) image to use in normalization, for before the sample is imaged
        :param flat_after: Flat (open beam) image to use in normalization, for after the sample is imaged
        :param dark_before: Dark image to use in normalization, for before the sample is imaged
        :param dark_after: Dark image to use in normalization, for before the sample is imaged
        :param selected_flat_fielding: Select which of the flat fielding methods to use, just Before stacks, just After
        stacks or combined.
        :param cores: The number of cores that will be used to process the data.
        :param chunksize: The number of chunks that each worker will receive.
        :return: Filtered data (stack of images)
        """
        h.check_data_stack(data)

        if selected_flat_fielding is not None:
            if selected_flat_fielding == "Both, concatenated":
                flat_avg = (flat_before.data.mean(axis=0) + flat_after.data.mean(axis=0)) / 2.0
                dark_avg = (dark_before.data.mean(axis=0) + dark_after.data.mean(axis=0)) / 2.0
            elif selected_flat_fielding == "Only Before":
                flat_avg = flat_before.data.mean(axis=0)
                dark_avg = dark_before.data.mean(axis=0)
            elif selected_flat_fielding == "Only After":
                flat_avg = flat_after.data.mean(axis=0)
                dark_avg = dark_after.data.mean(axis=0)
            else:
                flat_avg = None
                dark_avg = None

            if flat_avg is not None and dark_avg is not None:
                if 2 != flat_avg.ndim or 2 != dark_avg.ndim:
                    raise ValueError(
                        f"Incorrect shape of the flat image ({flat_avg.shape}) or dark image ({dark_avg.shape}) \
                        which should match the shape of the sample images ({data.data.shape})")

                if not data.data.shape[1:] == flat_avg.shape == dark_avg.shape:
                    raise ValueError(f"Not all images are the expected shape: {data.data.shape[1:]}, instead "
                                     f"flat had shape: {flat_avg.shape}, and dark had shape: {dark_avg.shape}")

                progress = Progress.ensure_instance(progress,
                                                    num_steps=data.data.shape[0],
                                                    task_name='Background Correction')
                _execute(data.data, flat_avg, dark_avg, cores, chunksize, progress)

        h.check_data_stack(data)
        return data

    @staticmethod
    def register_gui(form, on_change, view: FiltersWindowView) -> Dict[str, Any]:
        from mantidimaging.gui.utility import add_property_to_form

        def string_contains_all_parts(string: str, parts: list) -> bool:
            for part in parts:
                if part.lower() not in string:
                    return False
            return True

        def try_to_select_relevant_stack(name: str, widget: StackSelectorWidgetView) -> None:
            # Split based on whitespace
            name_parts = name.split()
            for i in range(widget.count()):
                # If widget text contains all name parts
                if string_contains_all_parts(widget.itemText(i).lower(), name_parts):
                    widget.setCurrentIndex(i)
                    break

        _, selected_flat_fielding_widget = add_property_to_form("Flat Fielding Method",
                                                                Type.CHOICE,
                                                                valid_values=["Only Before", "Only After",
                                                                              "Both, concatenated"],
                                                                form=form,
                                                                filters_view=view,
                                                                on_change=on_change,
                                                                tooltip="Choosing which stacks to use during flat "
                                                                        "fielding")

        _, flat_before_widget = add_property_to_form("Flat Before",
                                                     Type.STACK,
                                                     form=form,
                                                     filters_view=view,
                                                     on_change=on_change,
                                                     tooltip="Flat images to be used for correcting the flat field.")
        _, flat_after_widget = add_property_to_form("Flat After",
                                                    Type.STACK,
                                                    form=form,
                                                    filters_view=view,
                                                    on_change=on_change,
                                                    tooltip="Flat images to be used for correcting the flat field.")

        _, dark_before_widget = add_property_to_form("Dark Before",
                                                     Type.STACK,
                                                     form=form,
                                                     filters_view=view,
                                                     on_change=on_change,
                                                     tooltip="Dark images to be used for subtracting the background.")
        _, dark_after_widget = add_property_to_form("Dark After",
                                                    Type.STACK,
                                                    form=form,
                                                    filters_view=view,
                                                    on_change=on_change,
                                                    tooltip="Dark images to be used for subtracting the background.")

        assert isinstance(flat_before_widget, StackSelectorWidgetView)
        flat_before_widget.setMaximumWidth(375)
        flat_before_widget.subscribe_to_main_window(view.main_window)
        try_to_select_relevant_stack("Flat Before", flat_before_widget)

        assert isinstance(flat_after_widget, StackSelectorWidgetView)
        flat_after_widget.setMaximumWidth(375)
        flat_after_widget.subscribe_to_main_window(view.main_window)
        try_to_select_relevant_stack("Flat After", flat_after_widget)

        assert isinstance(dark_before_widget, StackSelectorWidgetView)
        dark_before_widget.setMaximumWidth(375)
        dark_before_widget.subscribe_to_main_window(view.main_window)
        try_to_select_relevant_stack("Dark Before", dark_before_widget)

        assert isinstance(dark_after_widget, StackSelectorWidgetView)
        dark_after_widget.setMaximumWidth(375)
        dark_after_widget.subscribe_to_main_window(view.main_window)
        try_to_select_relevant_stack("Dark After", dark_after_widget)

        return {
            'selected_flat_fielding_widget': selected_flat_fielding_widget,
            'flat_before_widget': flat_before_widget,
            'flat_after_widget': flat_after_widget,
            'dark_before_widget': dark_before_widget,
            'dark_after_widget': dark_after_widget,
        }

    @staticmethod
    def execute_wrapper(  # type: ignore
            flat_before_widget: StackSelectorWidgetView, flat_after_widget: StackSelectorWidgetView,
            dark_before_widget: StackSelectorWidgetView, dark_after_widget: StackSelectorWidgetView,
            selected_flat_fielding_widget) -> partial:
        flat_before_stack = flat_before_widget.main_window.get_stack_visualiser(flat_before_widget.current())
        flat_before_images = flat_before_stack.presenter.images
        flat_after_stack = flat_after_widget.main_window.get_stack_visualiser(flat_after_widget.current())
        flat_after_images = flat_after_stack.presenter.images

        dark_before_stack = dark_before_widget.main_window.get_stack_visualiser(dark_before_widget.current())
        dark_before_images = dark_before_stack.presenter.images
        dark_after_stack = dark_after_widget.main_window.get_stack_visualiser(dark_after_widget.current())
        dark_after_images = dark_after_stack.presenter.images

        selected_flat_fielding = selected_flat_fielding_widget.currentText()

        return partial(FlatFieldFilter.filter_func, flat_before=flat_before_images, flat_after=flat_after_images,
                       dark_before=dark_before_images, dark_after=dark_after_images,
                       selected_flat_fielding=selected_flat_fielding)

    @staticmethod
    def validate_execute_kwargs(kwargs):
        # Validate something is in both path text inputs
        if 'selected_flat_fielding_widget' not in kwargs:
            return False

        if 'flat_before_widget' not in kwargs and 'dark_before_widget' not in kwargs or\
                'flat_after_widget' not in kwargs and 'dark_after_widget' not in kwargs:
            return False
        assert isinstance(kwargs["flat_before_widget"], StackSelectorWidgetView)
        assert isinstance(kwargs["flat_after_widget"], StackSelectorWidgetView)
        assert isinstance(kwargs["dark_before_widget"], StackSelectorWidgetView)
        assert isinstance(kwargs["dark_after_widget"], StackSelectorWidgetView)
        return True


def _divide(data, norm_divide):
    np.true_divide(data, norm_divide, out=data)


def _subtract(data, dark=None):
    # specify out to do in place, otherwise the data is copied
    np.subtract(data, dark, out=data)


def _execute(data, flat=None, dark=None, cores=None, chunksize=None, progress=None):
    """A benchmark justifying the current implementation, performed on
    500x2048x2048 images.

    #1 Separate runs
    Subtract (sequential with np.subtract(data, dark, out=data)) - 13s
    Divide (par) - 1.15s

    #2 Separate parallel runs
    Subtract (par) - 5.5s
    Divide (par) - 1.15s

    #3 Added subtract into _divide so that it is:
                np.true_divide(
                    np.subtract(data, dark, out=data), norm_divide, out=data)
    Subtract then divide (par) - 55s
    """
    with progress:
        progress.update(msg="Applying background correction")

        with pu.temp_shared_array((1, data.shape[1], data.shape[2]), data.dtype) as norm_divide:
            # remove a dimension, I found this to be the easiest way to do it
            norm_divide = norm_divide.reshape(data.shape[1], data.shape[2])

            # subtract dark from flat and copy into shared array with [:]
            norm_divide[:] = np.subtract(flat, dark)

            # prevent divide-by-zero issues, and negative pixels make no sense
            norm_divide[norm_divide == 0] = MINIMUM_PIXEL_VALUE

            # subtract the dark from all images
            f = ptsm.create_partial(_subtract, fwd_function=ptsm.inplace_second_2d)
            data, dark = ptsm.execute(data, dark, f, cores, chunksize, progress=progress)

            # divide the data by (flat - dark)
            f = ptsm.create_partial(_divide, fwd_function=ptsm.inplace_second_2d)
            data, norm_divide = ptsm.execute(data, norm_divide, f, cores, chunksize, progress=progress)

    return data
