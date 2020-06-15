import os
from functools import partial
from logging import getLogger
from typing import Any, Dict

import numpy as np
from PyQt5.QtWidgets import QLineEdit

from mantidimaging import helper as h
from mantidimaging.core import io
from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import two_shared_mem as ptsm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.widgets.stack_selector import StackSelectorWidgetView
from mantidimaging.gui.windows.filters import FiltersWindowView

# The smallest and largest allowed pixel value
MINIMUM_PIXEL_VALUE = 1e-9
MAXIMUM_PIXEL_VALUE = 1e9


class FlatFieldFilter(BaseFilter):
    filter_name = 'Flat-fielding'

    @staticmethod
    def filter_func(data: Images,
                    flat: Images = None,
                    dark: Images = None,
                    clip_min=MINIMUM_PIXEL_VALUE,
                    clip_max=MAXIMUM_PIXEL_VALUE,
                    cores=None,
                    chunksize=None,
                    progress=None) -> Images:
        """
        Do background correction with flat and dark images.

        :param data: Sample data which is to be processed. Expected in radiograms
        :param flat: Flat (open beam) image to use in normalization
        :param dark: Dark image to use in normalization
        :param clip_min: After normalisation, clip any pixels under this value.
        :param clip_max: After normalisation, clip any pixels over this value.
        :param cores: The number of cores that will be used to process the data.
        :param chunksize: The number of chunks that each worker will receive.
        :return: Filtered data (stack of images)
        """
        h.check_data_stack(data)

        if flat is not None and dark is not None:
            flat_avg = flat.sample.mean(axis=0)
            dark_avg = dark.sample.mean(axis=0)
            if 2 != flat_avg.ndim or 2 != dark_avg.ndim:
                raise ValueError(
                    f"Incorrect shape of the flat image ({flat_avg.shape}) or dark image ({dark_avg.shape}) \
                    which should match the shape of the sample images ({data.sample.shape})")

            if not data.sample.shape[1:] == flat_avg.shape == dark_avg.shape:
                raise ValueError(f"Not all images are the expected shape: {data.sample.shape[1:]}, instead "
                                 f"flat had shape: {flat_avg.shape}, and dark had shape: {dark_avg.shape}")

            progress = Progress.ensure_instance(progress,
                                                num_steps=data.sample.shape[0],
                                                task_name='Background Correction')
            if pu.multiprocessing_necessary(data.sample.shape, cores):
                _execute_par(data.sample, flat_avg, dark_avg, clip_min, clip_max, cores, chunksize, progress)
            else:
                _execute_seq(data.sample, flat_avg, dark_avg, clip_min, clip_max, progress)

        h.check_data_stack(data)
        return data

    @staticmethod
    def register_gui(form, on_change, view: FiltersWindowView) -> Dict[str, Any]:
        from mantidimaging.gui.utility import add_property_to_form

        def try_to_select_relevant_stack(name: str, widget: StackSelectorWidgetView) -> None:
            for i in range(widget.count()):
                if name.lower() in widget.itemText(i).lower():
                    widget.setCurrentIndex(i)
                    break

        _, flat_widget = add_property_to_form("Flat", Type.STACK, form=form, filters_view=view, on_change=on_change)
        _, dark_widget = add_property_to_form("Dark", Type.STACK, form=form, filters_view=view, on_change=on_change)
        assert isinstance(flat_widget, StackSelectorWidgetView)
        assert isinstance(dark_widget, StackSelectorWidgetView)

        flat_widget.subscribe_to_main_window(view.main_window)
        try_to_select_relevant_stack("Flat", flat_widget)

        dark_widget.subscribe_to_main_window(view.main_window)
        try_to_select_relevant_stack("Dark", dark_widget)

        return {
            'flat_widget': flat_widget,
            'dark_widget': dark_widget,
        }

    @staticmethod
    def execute_wrapper(  # type: ignore
            flat_widget: StackSelectorWidgetView, dark_widget: StackSelectorWidgetView) -> partial:
        flat_stack = flat_widget.main_window.get_stack_visualiser(flat_widget.current())
        flat_images = flat_stack.presenter.images
        dark_stack = dark_widget.main_window.get_stack_visualiser(dark_widget.current())
        dark_images = dark_stack.presenter.images
        return partial(FlatFieldFilter.filter_func, flat=flat_images, dark=dark_images)

    @staticmethod
    def validate_execute_kwargs(kwargs):
        # Validate something is in both path text inputs
        if 'flat_widget' not in kwargs or 'dark_widget' not in kwargs:
            return False
        assert isinstance(kwargs["flat_widget"], StackSelectorWidgetView)
        assert isinstance(kwargs["dark_widget"], StackSelectorWidgetView)
        return True


def _divide(data, norm_divide):
    np.true_divide(data, norm_divide, out=data)


def _subtract(data, dark=None):
    # specify out to do in place, otherwise the data is copied
    np.subtract(data, dark, out=data)


def _execute_par(data,
                 flat=None,
                 dark=None,
                 clip_min=MINIMUM_PIXEL_VALUE,
                 clip_max=MAXIMUM_PIXEL_VALUE,
                 cores=None,
                 chunksize=None,
                 progress=None):
    """
    A benchmark justifying the current implementation, performed on
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
        progress.update(msg="Applying background correction.")

        with pu.temp_shared_array((1, data.shape[1], data.shape[2]), data.dtype) as norm_divide:
            # remove a dimension, I found this to be the easiest way to do it
            norm_divide = norm_divide.reshape(data.shape[1], data.shape[2])

            # subtract dark from flat and copy into shared array with [:]
            norm_divide[:] = np.subtract(flat, dark)

            # prevent divide-by-zero issues, and negative pixels make no sense
            norm_divide[norm_divide == 0] = MINIMUM_PIXEL_VALUE

            # subtract the dark from all images
            f = ptsm.create_partial(_subtract, fwd_function=ptsm.inplace_second_2d)
            data, dark = ptsm.execute(data, dark, f, cores, chunksize, "Subtract Dark", progress=progress)

            # divide the data by (flat - dark)
            f = ptsm.create_partial(_divide, fwd_function=ptsm.inplace_second_2d)
            data, norm_divide = ptsm.execute(data, norm_divide, f, cores, chunksize, "Norm by Flat", progress=progress)

            # After scaling back the values some images will have pixels with big
            # negative values -25626262 which throws off contrast adjustments.
            # This will crop those negative pixels out, and set them to nearly
            # zero.
            # The negative values will also get scaled back after this in
            # value_scaling which will increase their values further!
            np.clip(data, clip_min, clip_max, out=data)

    return data


def _execute_seq(data, flat=None, dark=None, clip_min=MINIMUM_PIXEL_VALUE, clip_max=MAXIMUM_PIXEL_VALUE, progress=None):
    with progress:
        progress.update(msg="Normalization by flat/dark images")

        norm_divide = np.subtract(flat, dark)

        # prevent divide-by-zero issues
        norm_divide[norm_divide == 0] = MINIMUM_PIXEL_VALUE
        np.subtract(data, dark, out=data)
        np.subtract(flat, dark, out=flat)
        np.true_divide(data, flat, out=data)
        np.clip(data, clip_min, clip_max, out=data)

    return data


def get_average_image(text_widget: 'QLineEdit'):
    log = getLogger(__name__)

    text = str(text_widget.text())
    prefix = io.utility.get_prefix(text)
    extension = io.utility.get_file_extension(text)
    directory = os.path.dirname(text)

    log.debug(f"Loading image from widget text: '{text}', directory: '{directory}', "
              f"prefix: '{prefix}', extension: '{extension}'")
    images_flat_only = io.loader.load(directory, in_prefix=prefix, in_format=extension)
    # this will be put in the 'sample' attribute, because we load a single
    # volume
    mean_image = images_flat_only.sample.mean(axis=0)
    images_flat_only.free_memory()
    return mean_image
