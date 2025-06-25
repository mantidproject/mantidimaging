# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Any, TYPE_CHECKING
from PyQt5.QtWidgets import QComboBox, QCheckBox

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView
from mantidimaging.core.operation_history.decorators import log_operation

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
    @log_operation
    def filter_func(images: ImageStack,
                    flat_before: ImageStack | None = None,
                    flat_after: ImageStack | None = None,
                    dark_before: ImageStack | None = None,
                    dark_after: ImageStack | None = None,
                    selected_flat_fielding: str | None = None,
                    use_dark: bool = True,
                    progress=None) -> ImageStack:
        """Do background correction with flat and dark images.
        :param images: Sample data which is to be processed. Expected in radiograms
        :param flat_before: Flat (open beam) image to use in normalization, collected before the sample was imaged
        :param flat_after: Flat (open beam) image to use in normalization, collected after the sample was imaged
        :param dark_before: Dark image to use in normalization, collected before the sample was imaged
        :param dark_after: Dark image to use in normalization, collected after the sample was imaged
        :param selected_flat_fielding: Select which of the flat fielding methods to use, just Before stacks, just After
                                       stacks or combined.
        :param use_dark: Whether to use dark frame subtraction
        :return: Filtered data (stack of images)
        """
        h.check_data_stack(images)
        if selected_flat_fielding not in ["Both, concatenated", "Only Before", "Only After"]:
            raise ValueError(f"Invalid flat fielding method: {selected_flat_fielding}")

        dark_avg = None

        if selected_flat_fielding == "Both, concatenated":
            if flat_before is None:
                raise ValueError("Missing stack: flat_before is required for 'Both, concatenated'")
            if flat_after is None:
                raise ValueError("Missing stack: flat_after is required for 'Both, concatenated'")
            flat_avg = (flat_before.data.mean(axis=0) + flat_after.data.mean(axis=0)) / 2.0
            if use_dark:
                if dark_before is None or dark_after is None:
                    raise ValueError("Missing stack: dark_before and dark_after are required for 'Both, concatenated'")
                dark_avg = (dark_before.data.mean(axis=0) + dark_after.data.mean(axis=0)) / 2.0

        elif selected_flat_fielding == "Only After":
            if flat_after is None:
                raise ValueError("Missing stack: flat_after is required for 'Only After'")
            flat_avg = flat_after.data.mean(axis=0)
            if use_dark:
                if dark_after is None:
                    raise ValueError("Missing stack: dark_after is required for 'Only After'")
                dark_avg = dark_after.data.mean(axis=0)

        elif selected_flat_fielding == "Only Before":
            if flat_before is None:
                raise ValueError("Missing stack: flat_before is required for 'Only Before'")
            flat_avg = flat_before.data.mean(axis=0)
            if use_dark:
                if dark_before is None:
                    raise ValueError("Missing stack: dark_before is required for 'Only Before'")
                dark_avg = dark_before.data.mean(axis=0)

        if dark_avg is None:
            dark_avg = np.zeros_like(flat_avg)

        if flat_avg is not None and dark_avg is not None:
            if flat_avg.ndim != 2 or dark_avg.ndim != 2:
                raise ValueError(
                    f"Incorrect shape of the flat image ({flat_avg.shape}) or dark image ({dark_avg.shape}) "
                    f"which should match the shape of the sample images ({images.data.shape[1:]})")
            if not (images.data.shape[1:] == flat_avg.shape == dark_avg.shape):
                raise ValueError(f"Not all images are the expected shape: {images.data.shape[1:]}, instead "
                                 f"flat had shape: {flat_avg.shape}, and dark had shape: {dark_avg.shape}")

        params = {'flat_avg': flat_avg, 'dark_avg': dark_avg}
        ps.run_compute_func(FlatFieldFilter._compute_flat_field, len(images.data), [images.shared_array], params)

        h.check_data_stack(images)
        return images

    @staticmethod
    def _compute_flat_field(index: int, array: np.ndarray, params: dict):
        flat_avg = params['flat_avg']
        dark_avg = params['dark_avg']

        norm_divide = flat_avg - dark_avg
        norm_divide[norm_divide == 0] = MINIMUM_PIXEL_VALUE
        array[index] -= dark_avg
        array[index] /= norm_divide

    @staticmethod
    def register_gui(form, on_change, view) -> dict[str, Any]:
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

        return partial(FlatFieldFilter.filter_func,
                       flat_before=flat_before_images,
                       flat_after=flat_after_images,
                       dark_before=dark_before_images,
                       dark_after=dark_after_images,
                       selected_flat_fielding=selected_flat_fielding,
                       use_dark=use_dark)

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
