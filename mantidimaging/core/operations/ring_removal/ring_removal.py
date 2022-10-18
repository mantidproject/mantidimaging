# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial

from PyQt5.QtWidgets import QComboBox

from mantidimaging import helper as h
from mantidimaging.core.data import ImageStack
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.utility.optional_imports import safe_import
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility.qt_helpers import Type


class RingRemovalFilter(BaseFilter):
    """Remove ring artifacts from images in the reconstructed domain.

    Intended to be used on: Reconstructed slices

    When: To remove ring-artifacts that have not been removed, or have been introduced
    by pre-processing
    """
    filter_name = "Ring Removal"
    link_histograms = True
    show_negative_overlay = False

    @staticmethod
    def filter_func(images: ImageStack,
                    center_mode="image center",
                    center_x=None,
                    center_y=None,
                    thresh=300.0,
                    thresh_max=300.0,
                    thresh_min=-100.0,
                    theta_min=30,
                    rwidth=30,
                    progress=None):
        """
        Removal of ring artifacts in reconstructed volume. Uses Wavelet-Fourier based ring removal

        :param images: Sample data which is to be processed. Expected in radiograms
        :param center_mode: Whether to use the center of the image or a user-defined value
        :param center_x: (float, optional) abscissa location of center of rotation
        :param center_y: (float, optional) ordinate location of center of rotation
        :param thresh: (float, optional)
                       maximum value of an offset due to a ring artifact
        :param thresh_max: (float, optional)
                       max value for portion of image to filter
        :param thresh_min: (float, optional)
                       min value for portion of image to filer
        :param theta_min: (int, optional)
                          minimum angle in degrees to be considered ring artifact
        :param rwidth: (int, optional)
                       Maximum width of the rings to be filtered in pixels
        :returns: Filtered data
        """
        progress = Progress.ensure_instance(progress, task_name='Ring Removal')

        tp = safe_import('tomopy.misc.corr')

        if center_mode != "manual":
            center_x = center_y = None

        h.check_data_stack(images)

        with progress:
            progress.update(msg="Ring Removal")
            sample = images.data
            tp.remove_ring(sample,
                           center_x=center_x,
                           center_y=center_y,
                           thresh=thresh,
                           thresh_max=thresh_max,
                           thresh_min=thresh_min,
                           theta_min=theta_min,
                           rwidth=rwidth,
                           out=sample)

        return images

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        range1 = (0, 1000000)
        range2 = (-1000000, 1000000)

        _, center_mode = add_property_to_form('Center of rotation',
                                              Type.CHOICE,
                                              valid_values=["image center", "manual"],
                                              form=form,
                                              on_change=on_change,
                                              tooltip="Use image center or enter manually")

        _, x_field = add_property_to_form('Center of rotation X position',
                                          Type.INT,
                                          valid_values=range1,
                                          form=form,
                                          on_change=on_change,
                                          tooltip="abscissa location of center of rotation")

        _, y_field = add_property_to_form('Center of rotation Y position',
                                          Type.INT,
                                          valid_values=range1,
                                          form=form,
                                          on_change=on_change,
                                          tooltip="ordinate location of center of rotation")

        _, thresh = add_property_to_form('Threshold',
                                         Type.FLOAT,
                                         valid_values=range2,
                                         form=form,
                                         on_change=on_change,
                                         tooltip="maximum value of an offset due to a ring artifact")

        _, thresh_min = add_property_to_form('Threshold Min',
                                             Type.FLOAT,
                                             valid_values=range2,
                                             form=form,
                                             on_change=on_change,
                                             tooltip="min value for portion of image to filter")

        _, thresh_max = add_property_to_form('Threshold Max',
                                             Type.FLOAT,
                                             valid_values=range2,
                                             form=form,
                                             on_change=on_change,
                                             tooltip="max value for portion of image to filter")

        _, theta = add_property_to_form('Theta',
                                        Type.INT,
                                        valid_values=(0, 179),
                                        form=form,
                                        on_change=on_change,
                                        tooltip="minimum angle in degrees to be considered ring artifact")

        _, rwidth = add_property_to_form('RWidth',
                                         Type.INT,
                                         valid_values=range2,
                                         form=form,
                                         on_change=on_change,
                                         tooltip="Maximum width of the rings to be filtered in pixels")

        def enable_center():
            if center_mode.currentText() == "manual":
                x_field.setEnabled(True)
                y_field.setEnabled(True)
            else:
                x_field.setEnabled(False)
                y_field.setEnabled(False)

        assert (isinstance(center_mode, QComboBox))
        center_mode.currentIndexChanged.connect(enable_center)
        enable_center()

        return {
            "center_mode": center_mode,
            "x_field": x_field,
            "y_field": y_field,
            "thresh": thresh,
            "thresh_min": thresh_min,
            "thresh_max": thresh_max,
            "theta": theta,
            "rwidth": rwidth,
        }

    @staticmethod
    def execute_wrapper(center_mode=None,
                        x_field=None,
                        y_field=None,
                        thresh=None,
                        thresh_max=None,
                        thresh_min=None,
                        theta=None,
                        rwidth=None):
        return partial(RingRemovalFilter.filter_func,
                       center_mode=center_mode.currentText(),
                       center_x=x_field.value(),
                       center_y=y_field.value(),
                       thresh=thresh.value(),
                       thresh_max=thresh_max.value(),
                       thresh_min=thresh_min.value(),
                       theta_min=theta.value(),
                       rwidth=rwidth.value())
