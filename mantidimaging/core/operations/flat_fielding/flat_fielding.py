# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Any, Dict, TYPE_CHECKING
from PyQt5.QtWidgets import QComboBox, QCheckBox

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import utility as pu, shared as ps
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack

# The smallest and largest allowed pixel value
MINIMUM_PIXEL_VALUE = 1e-9
MAXIMUM_PIXEL_VALUE = 1e9
valid_methods = ["Only Before", "Only After", "Both, concatenated"]


def enable_correct_fields_only(selected_flat_fielding_widget, flat_before_widget, flat_after_widget, dark_before_widget,
                               dark_after_widget, use_dark_frame):
    text = selected_flat_fielding_widget.currentText()
    use_dark = use_dark_frame.isChecked()
    if text == "Only Before":
        flat_before_widget.setEnabled(True)
        flat_after_widget.setEnabled(False)
        dark_before_widget.setEnabled(use_dark)
        dark_after_widget.setEnabled(False)
    elif text == "Only After":
        flat_before_widget.setEnabled(False)
        flat_after_widget.setEnabled(True)
        dark_before_widget.setEnabled(False)
        dark_after_widget.setEnabled(use_dark)
    elif text == "Both, concatenated":
        flat_before_widget.setEnabled(True)
        flat_after_widget.setEnabled(True)
        dark_before_widget.setEnabled(use_dark)
        dark_after_widget.setEnabled(use_dark)
    else:
        raise RuntimeError("Unknown field parameter")


class FlatFieldFilter(BaseFilter):
    """Uses the flat (open beam) and dark images to normalise a stack of images (radiograms, projections),
    and to correct for a beam profile, scintillator imperfections and/or  detector inhomogeneities. This
    operation produces images of transmission values.

    In practice, several open beam and dark images are averaged in the flat-fielding process.

    Intended to be used on: Projections

    When: As one of the first pre-processing steps

    Caution: Make sure the correct stacks are selected for flat and dark.

    Caution: Check that the flat and dark images don't have any very bright pixels,
    or this will introduce additional noise in the sample. Remove outliers before flat-fielding.
    """
    filter_name = 'Flat-fielding'

    @staticmethod
    def filter_func(cls,
                    images: ImageStack,
                    flat_before: ImageStack | None = None,
                    flat_after: ImageStack | None = None,
                    dark_before: ImageStack | None = None,
                    dark_after: ImageStack | None = None,
                    selected_flat_fielding: str | None = None,
                    use_dark: bool = True,
                    progress=None) -> ImageStack:

        h.check_data_stack(images)

        if selected_flat_fielding == "Both, concatenated" and flat_after is not None and flat_before is not None \
                and dark_after is not None and dark_before is not None:
            flat_avg = (flat_before.data.mean(axis=0) + flat_after.data.mean(axis=0)) / 2.0
            if use_dark:
                dark_avg = (dark_before.data.mean(axis=0) + dark_after.data.mean(axis=0)) / 2.0
        elif selected_flat_fielding == "Only Before" and flat_before is not None and dark_before is not None:
            flat_avg = flat_before.data.mean(axis=0)
            if use_dark:
                dark_avg = dark_before.data.mean(axis=0)
        elif selected_flat_fielding == "Only After" and flat_after is not None and dark_after is not None:
            flat_avg = flat_after.data.mean(axis=0)
            if use_dark:
                dark_avg = dark_after.data.mean(axis=0)
        else:
            raise ValueError("selected_flat_fielding not in:", valid_methods)

        if not use_dark:
            dark_avg = np.zeros_like(flat_avg)

        if flat_avg is not None and dark_avg is not None:
            if 2 != flat_avg.ndim or 2 != dark_avg.ndim:
                raise ValueError(
                    f"Incorrect shape of the flat image ({flat_avg.shape}) or dark image ({dark_avg.shape}) \
                    which should match the shape of the sample images ({images.data.shape})")

            if not images.data.shape[1:] == flat_avg.shape == dark_avg.shape:
                raise ValueError(f"Not all images are the expected shape: {images.data.shape[1:]}, instead "
                                 f"flat had shape: {flat_avg.shape}, and dark had shape: {dark_avg.shape}")

            progress = Progress.ensure_instance(progress,
                                                num_steps=images.data.shape[0],
                                                task_name='Background Correction')
            _execute(images, flat_avg, dark_avg, progress)

        h.check_data_stack(images)
        return images

    @staticmethod
    def register_gui(form, on_change, view) -> Dict[str, Any]:
        from mantidimaging.gui.utility import add_property_to_form

        _, selected_flat_fielding_widget = add_property_to_form("Flat Fielding Method",
                                                                Type.CHOICE,
                                                                valid_values=valid_methods,
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

        _, use_dark_widget = add_property_to_form("Use Dark Frame",
                                                  Type.BOOL,
                                                  default_value=True,
                                                  form=form,
                                                  filters_view=view,
                                                  on_change=on_change,
                                                  tooltip="Use dark frame subtraction")

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

        assert isinstance(flat_before_widget, DatasetSelectorWidgetView)
        flat_before_widget.setMaximumWidth(375)
        flat_before_widget.subscribe_to_main_window(view.main_window)
        flat_before_widget.try_to_select_relevant_stack("Flat")
        flat_before_widget.try_to_select_relevant_stack("Flat Before")

        assert isinstance(flat_after_widget, DatasetSelectorWidgetView)
        flat_after_widget.setMaximumWidth(375)
        flat_after_widget.subscribe_to_main_window(view.main_window)
        flat_after_widget.try_to_select_relevant_stack("Flat After")
        flat_after_widget.setEnabled(False)

        assert isinstance(dark_before_widget, DatasetSelectorWidgetView)
        dark_before_widget.setMaximumWidth(375)
        dark_before_widget.subscribe_to_main_window(view.main_window)
        dark_before_widget.try_to_select_relevant_stack("Dark")
        dark_before_widget.try_to_select_relevant_stack("Dark Before")

        assert isinstance(dark_after_widget, DatasetSelectorWidgetView)
        dark_after_widget.setMaximumWidth(375)
        dark_after_widget.subscribe_to_main_window(view.main_window)
        dark_after_widget.try_to_select_relevant_stack("Dark After")
        dark_after_widget.setEnabled(False)

        # Ensure that fields that are not currently used are disabled
        assert (isinstance(selected_flat_fielding_widget, QComboBox))
        selected_flat_fielding_widget.currentTextChanged.connect(lambda text: enable_correct_fields_only(
            selected_flat_fielding_widget, flat_before_widget, flat_after_widget, dark_before_widget, dark_after_widget,
            use_dark_widget))

        assert (isinstance(use_dark_widget, QCheckBox))
        use_dark_widget.stateChanged.connect(lambda text: enable_correct_fields_only(
            selected_flat_fielding_widget, flat_before_widget, flat_after_widget, dark_before_widget, dark_after_widget,
            use_dark_widget))

        return {
            'selected_flat_fielding_widget': selected_flat_fielding_widget,
            'flat_before_widget': flat_before_widget,
            'flat_after_widget': flat_after_widget,
            'dark_before_widget': dark_before_widget,
            'dark_after_widget': dark_after_widget,
            'use_dark_widget': use_dark_widget,
        }

    @staticmethod
    def execute_wrapper(  # type: ignore
            flat_before_widget: DatasetSelectorWidgetView, flat_after_widget: DatasetSelectorWidgetView,
            dark_before_widget: DatasetSelectorWidgetView, dark_after_widget: DatasetSelectorWidgetView,
            selected_flat_fielding_widget: QComboBox, use_dark_widget: QCheckBox) -> partial:

        flat_before_images = BaseFilter.get_images_from_stack(flat_before_widget, "flat before")
        flat_after_images = BaseFilter.get_images_from_stack(flat_after_widget, "flat after")

        dark_before_images = BaseFilter.get_images_from_stack(dark_before_widget, "dark before")
        dark_after_images = BaseFilter.get_images_from_stack(dark_after_widget, "dark after")

        selected_flat_fielding = selected_flat_fielding_widget.currentText()
        use_dark = use_dark_widget.isChecked()

        def wrapper(cls, images: ImageStack, progress=None) -> ImageStack:
            return cls.filter_func(images,
                                   flat_before=flat_before_images,
                                   flat_after=flat_after_images,
                                   dark_before=dark_before_images,
                                   dark_after=dark_after_images,
                                   selected_flat_fielding=selected_flat_fielding,
                                   use_dark=use_dark,
                                   progress=progress)

        return wrapper

    @staticmethod
    def validate_execute_kwargs(kwargs):
        # Validate something is in both path text inputs
        if 'selected_flat_fielding_widget' not in kwargs:
            return False

        if 'flat_before_widget' not in kwargs and 'dark_before_widget' not in kwargs or\
                'flat_after_widget' not in kwargs and 'dark_after_widget' not in kwargs:
            return False
        assert isinstance(kwargs["flat_before_widget"], DatasetSelectorWidgetView)
        assert isinstance(kwargs["flat_after_widget"], DatasetSelectorWidgetView)
        assert isinstance(kwargs["dark_before_widget"], DatasetSelectorWidgetView)
        assert isinstance(kwargs["dark_after_widget"], DatasetSelectorWidgetView)
        return True

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Basic


def _divide(data, norm_divide):
    np.true_divide(data, norm_divide, out=data)


def _subtract(data, dark=None):
    # specify out to do in place, otherwise the data is copied
    np.subtract(data, dark, out=data)


def _norm_divide(flat: np.ndarray, dark: np.ndarray) -> np.ndarray:
    # subtract dark from flat
    return np.subtract(flat, dark)


def _execute(cls, images: ImageStack, flat=None, dark=None, progress=None):
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

        if images.uses_shared_memory:
            shared_dark = pu.copy_into_shared_memory(dark)
            norm_divide = pu.copy_into_shared_memory(cls._norm_divide(flat, dark))
        else:
            shared_dark = pu.SharedArray(dark, None)
            norm_divide = pu.SharedArray(cls._norm_divide(flat, dark), None)

        # Prevent divide-by-zero issues
        norm_divide.array[norm_divide.array == 0] = cls.MINIMUM_PIXEL_VALUE

        # Subtract the dark from all images
        do_subtract = ps.create_partial(cls._subtract, fwd_function=ps.inplace_second_2d)
        arrays = [images.shared_array, shared_dark]
        ps.execute(do_subtract, arrays, images.data.shape[0], progress)

        # Divide the data by (flat - dark)
        do_divide = ps.create_partial(cls._divide, fwd_function=ps.inplace_second_2d)
        arrays = [images.shared_array, norm_divide]
        ps.execute(do_divide, arrays, images.data.shape[0], progress)

    return images
