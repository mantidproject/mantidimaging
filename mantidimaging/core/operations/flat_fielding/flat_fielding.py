# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import Any, Dict, TYPE_CHECKING
from PyQt5.QtWidgets import QComboBox, QCheckBox

import numpy as np

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
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
    filter_name = 'Flat-fielding'

    @classmethod
    def filter_func(cls,
                    images: ImageStack,
                    flat_before: ImageStack | None = None,
                    flat_after: ImageStack | None = None,
                    dark_before: ImageStack | None = None,
                    dark_after: ImageStack | None = None,
                    selected_flat_fielding: str | None = None,
                    use_dark: bool = True,
                    progress=None) -> ImageStack:

        if images.num_projections < 2:
            return images

        params = {
            "flat_before": flat_before,
            "flat_after": flat_after,
            "dark_before": dark_before,
            "dark_after": dark_after,
            "selected_flat_fielding": selected_flat_fielding,
            "use_dark": use_dark
        }

        ps.run_compute_func(cls.compute_function, images.num_sinograms, images.shared_array, params, progress)

        return images

    @staticmethod
    def compute_function(index: int, array: np.ndarray, params: Dict[str, Any]):
        flat_before = params["flat_before"]
        flat_after = params["flat_after"]
        dark_before = params["dark_before"]
        dark_after = params["dark_after"]
        selected_flat_fielding = params["selected_flat_fielding"]
        use_dark = params["use_dark"]

        if selected_flat_fielding == "Only Before":
            flat_image = flat_before.data[index] if flat_before is not None else None
            dark_image = dark_before.data[index] if dark_before is not None else None
        elif selected_flat_fielding == "Only After":
            flat_image = flat_after.data[index] if flat_after is not None else None
            dark_image = dark_after.data[index] if dark_after is not None else None
        elif selected_flat_fielding == "Both, concatenated":
            flat_image = (flat_before.data[index] + flat_after.data[index]) / 2.0 \
                if flat_before is not None and flat_after is not None else None
            dark_image = (dark_before.data[index] + dark_after.data[index]) / 2.0 \
                if dark_before is not None and dark_after is not None else None
        else:
            raise ValueError("Unknown flat fielding method")

        if flat_image is not None and dark_image is not None:
            corrected_flat = flat_image - dark_image
            corrected_flat[corrected_flat <= 0] = MINIMUM_PIXEL_VALUE
            corrected_data = np.divide(array, corrected_flat, out=np.zeros_like(array), where=(corrected_flat != 0))
            if use_dark:
                corrected_data -= dark_image
            np.clip(corrected_data, MINIMUM_PIXEL_VALUE, MAXIMUM_PIXEL_VALUE, out=corrected_data)
            array[:] = corrected_data

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

        return partial(FlatFieldFilter.filter_func,
                       flat_before=flat_before_images,
                       flat_after=flat_after_images,
                       dark_before=dark_before_images,
                       dark_after=dark_after_images,
                       selected_flat_fielding=selected_flat_fielding,
                       use_dark=use_dark)

    @staticmethod
    def validate_execute_kwargs(kwargs):
        if 'selected_flat_fielding_widget' not in kwargs:
            return False

        if ('flat_before_widget' not in kwargs or 'dark_before_widget' not in kwargs) \
                or ('flat_after_widget' not in kwargs or 'dark_after_widget' not in kwargs):
            return False

        return True

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Basic
