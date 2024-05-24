# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import numpy as np
from mantidimaging import helper as h
from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack


def modes() -> list[str]:
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
    def filter_func(images: ImageStack,
                    region_of_interest: SensibleROI | None = None,
                    normalisation_mode: str = DEFAULT_NORMALISATION_MODE,
                    flat_field: ImageStack | None = None,
                    progress=None):
        """Normalise by beam intensity.
        This does NOT do any checks if the Air Region is out of bounds!
        If the Air Region is out of bounds, the crop will fail at runtime.
        If the Air Region is in bounds, but has overlapping coordinates
        the crop give back a 0 shape of the coordinates that were wrong.
        :param images: Sample data which is to be processed. Expected in radiograms
        :param region_of_interest: The order is - Left Top Right Bottom. The air
        region for which grey values are summed up and used for normalisation/scaling.
        :param normalisation_mode: Controls what the ROI counts are normalised to.
            'Stack Average' : The mean value of the air region across all projections is preserved.
            'Flat Field' : The mean value of the air regions in the projections is made equal to the mean value of the
                           air region in the flat field image.
        :param flat_field: Flat field to use if 'Flat Field' mode is enabled.
        :param progress: Reference to a progress bar object
        :returns: Filtered data (stack of images)
        """
        if not region_of_interest:
            raise ValueError('region_of_interest must be provided')

        if isinstance(region_of_interest, list):
            region_of_interest = SensibleROI.from_list(region_of_interest)

        h.check_data_stack(images)

        global_params = RoiNormalisationFilter.calculate_global(images, region_of_interest, normalisation_mode,
                                                                flat_field)

        params = {
            'region_of_interest': region_of_interest,
            'normalisation_mode': normalisation_mode,
            'global_params': global_params
        }

        print("Filter Function Params:", params)

        ps.run_compute_func(RoiNormalisationFilter.compute_function, images.data.shape[0], images.shared_array, params)

        h.check_data_stack(images)

        return images

    @staticmethod
    def calculate_global(images, region_of_interest, normalisation_mode, flat_field):
        global_params = {}
        if normalisation_mode == 'Stack Average':
            air_means = np.array([
                RoiNormalisationFilter._calc_mean(images.data[i], region_of_interest.left, region_of_interest.top,
                                                  region_of_interest.right, region_of_interest.bottom)
                for i in range(images.data.shape[0])
            ])
            global_params['global_mean'] = np.mean(air_means)
        elif normalisation_mode == 'Flat Field' and flat_field is not None:
            flat_field_mean = RoiNormalisationFilter._calc_mean(flat_field.data, region_of_interest.left,
                                                                region_of_interest.top, region_of_interest.right,
                                                                region_of_interest.bottom)
            global_params['flat_field_mean'] = flat_field_mean
        else:
            raise ValueError(f"Unknown normalisation_mode: {normalisation_mode}")

        print("Global Params:", global_params)

        return global_params

    @staticmethod
    def compute_function(i: int, array: np.ndarray, params):
        region_of_interest = params['region_of_interest']
        normalisation_mode = params['normalisation_mode']
        global_params = params['global_params']

        air_mean = RoiNormalisationFilter._calc_mean(array[i], region_of_interest.left, region_of_interest.top,
                                                     region_of_interest.right, region_of_interest.bottom)

        print(f"Image {i} Air Mean: {air_mean}")

        if normalisation_mode == 'Stack Average':
            normalization_factor = global_params['global_mean'] / air_mean
            print(f"Image {i} Stack Average Normalization Factor: {normalization_factor}")
            array[i] *= normalization_factor
        elif normalisation_mode == 'Flat Field':
            normalization_factor = global_params['flat_field_mean'] / air_mean
            print(f"Image {i} Flat Field Normalization Factor: {normalization_factor}")
            array[i] *= normalization_factor
        else:
            raise ValueError(f"Unknown normalisation_mode: {normalisation_mode}")

    @staticmethod
    def _calc_mean(data, air_left=None, air_top=None, air_right=None, air_bottom=None):
        return data[air_top:air_bottom, air_left:air_right].mean()

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
