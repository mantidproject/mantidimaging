# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import List, Optional, TYPE_CHECKING, Dict, Any

import numpy as np

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack


def modes() -> List[str]:
    return ['Stack Average', 'Flat Field']


DEFAULT_NORMALISATION_MODE = modes()[0]


class RoiNormalisationFilter(BaseFilter):
    """Normalises the image data by using the average value in a no-sample (air) region of interest (ROI) of the
    image. This scaling operation allows to account for beam fluctuations and different exposure times of
    projections.

    Intended to be used on: Projections

    When: Always, to ensure that any fluctuations in beam intensity are normalised.

    Note: Beam fluctuations are visible by horizontal lines in the sinograms, as  some projections are
    brighter/darker than the neighbours. This can be fixed with this operation.
    """
    filter_name = "ROI Normalisation"
    link_histograms = True

    @staticmethod
    def calculate_flat_field_mean(flat_field: ImageStack) -> float:
        return np.mean(flat_field.data)

    @staticmethod
    def filter_func(images: ImageStack,
                    region_of_interest: SensibleROI | None = None,
                    normalisation_mode: str = DEFAULT_NORMALISATION_MODE,
                    flat_field: Optional[ImageStack] = None,
                    progress=None) -> ImageStack:
        flat_field_mean = None
        if normalisation_mode == "Flat Field" and flat_field is not None:
            flat_field_mean = RoiNormalisationFilter.calculate_flat_field_mean(flat_field)

        params = {
            'air_region': region_of_interest,
            'normalisation_mode': normalisation_mode,
            'flat_field_mean': flat_field_mean
        }

        ps.run_compute_func(RoiNormalisationFilter.compute_function, len(images.data), images.data, params)

        return images

    @staticmethod
    def compute_function(image_index: int, array: np.ndarray, params: Dict[str, Any]):
        air_region = params['air_region']
        normalisation_mode = params['normalisation_mode']
        flat_field_mean = params['flat_field_mean'] if 'flat_field_mean' in params else None

        air_values = array[image_index][air_region.top:air_region.bottom, air_region.left:air_region.right]
        air_mean = np.mean(air_values)

        if normalisation_mode == "Stack Average":
            normalization_factor = air_mean
        elif normalisation_mode == "Flat Field":
            if flat_field_mean is None:
                raise ValueError("flat_field_mean must be provided for 'Flat Field' normalisation mode")
            normalization_factor = air_mean / flat_field_mean
        else:
            raise ValueError(f"Unsupported normalisation_mode: {normalisation_mode}")

        array[image_index] /= normalization_factor

    @staticmethod
    def register_gui(form, on_change, view):
        label, roi_field = add_property_to_form("Air Region",
                                                Type.STR,
                                                form=form,
                                                on_change=on_change,
                                                default_value="0, 0, 200, 200")
        roi_button, _ = add_property_to_form("Select Air Region", "button", form=form, on_change=on_change)
        roi_button.clicked.connect(lambda: view.roi_visualiser(roi_field, roi_button))

        _, mode_field = add_property_to_form('Normalise Mode',
                                             Type.CHOICE,
                                             valid_values=modes(),
                                             form=form,
                                             on_change=on_change,
                                             tooltip="Method to normalise output values")

        _, flat_field_widget = add_property_to_form("Flat file",
                                                    Type.STACK,
                                                    form=form,
                                                    filters_view=view,
                                                    on_change=on_change,
                                                    tooltip="Flat images to be used for normalising.")

        assert isinstance(flat_field_widget, DatasetSelectorWidgetView)
        flat_field_widget.setMaximumWidth(375)
        flat_field_widget.subscribe_to_main_window(view.main_window)
        flat_field_widget.try_to_select_relevant_stack("Flat")
        flat_field_widget.try_to_select_relevant_stack("Flat Before")

        flat_field_widget.setEnabled(False)
        mode_field.currentTextChanged.connect(lambda text: enable_correct_fields_only(text, flat_field_widget))

        return {'roi_field': roi_field, 'norm_mode': mode_field, 'flat_field': flat_field_widget}

    @staticmethod
    def execute_wrapper(roi_field, norm_mode, flat_field):
        try:
            roi = SensibleROI.from_list([int(number) for number in roi_field.text().strip("[").strip("]").split(",")])
        except Exception as exc:
            raise ValueError(f"The provided ROI string is invalid! Error: {exc}") from exc

        mode = norm_mode.currentText()
        flat_images = BaseFilter.get_images_from_stack(flat_field, "flat field")
        return partial(RoiNormalisationFilter.filter_func,
                       region_of_interest=roi,
                       normalisation_mode=mode,
                       flat_field=flat_images)

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Basic


def enable_correct_fields_only(text, flat_file_widget):
    if text == "Flat Field":
        flat_file_widget.setEnabled(True)
    else:
        flat_file_widget.setEnabled(False)
