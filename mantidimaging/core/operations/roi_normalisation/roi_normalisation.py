# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial
from logging import getLogger
from typing import List, Optional

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.data import ImageStack
from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.parallel import shared as ps
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.sensible_roi import SensibleROI
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView


def modes() -> List[str]:
    return ['Stack Average', 'Flat Field']


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
                    region_of_interest: SensibleROI = None,
                    normalisation_mode: str = modes()[0],
                    flat_field: Optional[ImageStack] = None,
                    cores=None,
                    chunksize=None,
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

        :param cores: The number of cores that will be used to process the data.

        :param chunksize: The number of chunks that each worker will receive.
        :param progress: Reference to a progress bar object

        :returns: Filtered data (stack of images)
        """
        if normalisation_mode not in modes():
            raise ValueError(f"Unknown normalisation_mode: {normalisation_mode}, should be one of {modes()}")

        if normalisation_mode == "Flat Field" and flat_field is None:
            raise ValueError('flat_field must provided if using normalisation_mode of "Flat Field"')

        h.check_data_stack(images)

        if not region_of_interest:
            raise ValueError('region_of_interest must be provided')

        progress = Progress.ensure_instance(progress, task_name='ROI Normalisation')
        _execute(images, region_of_interest, normalisation_mode, flat_field, cores, chunksize, progress)
        h.check_data_stack(images)
        return images

    @staticmethod
    def register_gui(form, on_change, view):
        label, roi_field = add_property_to_form("Air Region",
                                                Type.STR,
                                                form=form,
                                                on_change=on_change,
                                                default_value="0, 0, 200, 200")
        add_property_to_form("Select Air Region",
                             "button",
                             form=form,
                             on_change=on_change,
                             run_on_press=lambda: view.roi_visualiser(roi_field))

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
        except Exception as e:
            raise ValueError(f"The provided ROI string is invalid! Error: {e}")

        mode = norm_mode.currentText()
        flat_images = BaseFilter.get_images_from_stack(flat_field, "flat field")
        return partial(RoiNormalisationFilter.filter_func,
                       region_of_interest=roi,
                       normalisation_mode=mode,
                       flat_field=flat_images)

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Basic


def _calc_mean(data, air_left=None, air_top=None, air_right=None, air_bottom=None):
    return data[air_top:air_bottom, air_left:air_right].mean()


def _divide_by_air(data=None, air_sums=None):
    data[:] = np.true_divide(data, air_sums)


def _execute(images: ImageStack,
             air_region: SensibleROI,
             normalisation_mode: str,
             flat_field: Optional[ImageStack],
             cores=None,
             chunksize=None,
             progress=None):
    log = getLogger(__name__)

    with progress:
        progress.update(msg="Normalization by air region")
        if isinstance(air_region, list):
            air_region = SensibleROI.from_list(air_region)

        # initialise same number of air sums
        img_num = images.data.shape[0]
        air_means = pu.create_array((img_num, ), images.dtype)

        do_calculate_air_means = ps.create_partial(_calc_mean,
                                                   ps.return_to_second_at_i,
                                                   air_left=air_region.left,
                                                   air_top=air_region.top,
                                                   air_right=air_region.right,
                                                   air_bottom=air_region.bottom)

        arrays = [images.shared_array, air_means]
        ps.execute(do_calculate_air_means, arrays, images.data.shape[0], progress, cores=cores)

        if normalisation_mode == 'Stack Average':
            air_means.array /= air_means.array.mean()

        elif normalisation_mode == 'Flat Field' and flat_field is not None:
            flat_mean = pu.create_array((flat_field.data.shape[0], ), flat_field.dtype)
            arrays = [flat_field.shared_array, flat_mean]
            ps.execute(do_calculate_air_means, arrays, flat_field.data.shape[0], progress, cores=cores)
            air_means.array /= flat_mean.array.mean()

        if np.isnan(air_means.array).any():
            raise ValueError("Air region contains invalid (NaN) pixels")

        do_divide = ps.create_partial(_divide_by_air, fwd_function=ps.inplace2)
        arrays = [images.shared_array, air_means]
        ps.execute(do_divide, arrays, images.data.shape[0], progress, cores=cores)

        avg = np.average(air_means.array)
        max_avg = np.max(air_means.array) / avg
        min_avg = np.min(air_means.array) / avg

        log.info(f"Normalization by air region. " f"Average: {avg}, max ratio: {max_avg}, min ratio: {min_avg}.")


def enable_correct_fields_only(text, flat_file_widget):
    if text == "Flat Field":
        flat_file_widget.setEnabled(True)
    else:
        flat_file_widget.setEnabled(False)
