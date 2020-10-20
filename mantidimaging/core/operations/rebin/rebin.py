from functools import partial
from typing import Optional

import numpy
import skimage.transform

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import two_shared_mem as ptsm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type


class RebinFilter(BaseFilter):
    """
    This filter temporarily increases memory usage, while the image is being rebinned.
    The memory usage will be lowered after the filter has finished executing.
    """
    filter_name = "Rebin"

    @staticmethod
    def filter_func(images: Images, rebin_param=0.5, mode=None, cores=None, chunksize=None, progress=None) -> Images:
        """
        :param images: Sample data which is to be processed. Expects radiograms
        :param rebin_param: int, float or tuple
                            int - Percentage of current size.
                            float - Fraction of current size.
                            tuple - Size of the output image (x, y).
        :param mode: Interpolation to use for re-sizing
                     ('nearest', 'lanczos', 'bilinear', 'bicubic' or 'cubic').
        :param cores: The number of cores that will be used to process the data.
        :param chunksize: The number of chunks that each worker will receive.

        :return: The processed 3D numpy.ndarray
        """
        h.check_data_stack(images)

        if isinstance(rebin_param, tuple):
            param_valid = rebin_param[0] > 0 and rebin_param[1] > 0
        else:
            param_valid = rebin_param > 0

        if param_valid:
            sample = images.data
            sample_name: Optional[str]
            # allocate output first BEFORE freeing the original data,
            # otherwise it's possible to free and then fail allocation for output
            # at which point you're left with no data
            empty_resized_data = _create_reshaped_array(images, rebin_param)

            f = ptsm.create_partial(skimage.transform.resize,
                                    ptsm.return_to_second_but_dont_use_it,
                                    mode=mode,
                                    output_shape=empty_resized_data.shape[1:])
            ptsm.execute(sample, empty_resized_data, f, cores, chunksize, progress=progress, msg="Applying Rebin")
            images.data = empty_resized_data

        return images

    @staticmethod
    def register_gui(form, on_change, view):
        # Rebin by uniform factor options
        _, factor = add_property_to_form('Factor',
                                         'float',
                                         0.5, (0.0, 1.0),
                                         on_change=on_change,
                                         tooltip="Factor by which the data will be rebinned, "
                                                 "e.g. 0.5 is 50% reduced size")
        factor.setSingleStep(0.05)

        # Rebin to target shape options
        shape_range = (0, 9999)

        _, shape_x = add_property_to_form('X', Type.INT, valid_values=shape_range, on_change=on_change)
        _, shape_y = add_property_to_form('Y', Type.INT, valid_values=shape_range, on_change=on_change)

        from PyQt5 import Qt
        shape_fields = Qt.QHBoxLayout()
        shape_fields.addWidget(shape_x)
        shape_fields.addWidget(shape_y)

        # Rebin dimension selection options
        rebin_by_factor_radio = Qt.QRadioButton("Rebin by Factor")

        def size_by_factor_toggled(enabled):
            factor.setEnabled(enabled)
            on_change()

        rebin_by_factor_radio.toggled.connect(size_by_factor_toggled)

        rebin_to_dimensions_radio = Qt.QRadioButton("Rebin to Dimensions")

        def size_by_dimensions_toggled(enabled):
            shape_x.setEnabled(enabled)
            shape_y.setEnabled(enabled)
            on_change()

        rebin_to_dimensions_radio.toggled.connect(size_by_dimensions_toggled)

        # Rebin mode options
        label_mode = Qt.QLabel("Mode")
        mode_field = Qt.QComboBox()
        mode_field.addItems(modes())

        form.addRow(rebin_to_dimensions_radio, shape_fields)
        form.addRow(rebin_by_factor_radio, factor)
        form.addRow(label_mode, mode_field)

        # Ensure good default UI state
        rebin_to_dimensions_radio.setChecked(True)
        rebin_by_factor_radio.setChecked(True)

        return {
            "rebin_to_dimensions_radio": rebin_to_dimensions_radio,
            "shape_x": shape_x,
            "shape_y": shape_y,
            "rebin_by_factor_radio": rebin_by_factor_radio,
            "factor": factor,
            "mode_field": mode_field,
        }

    @staticmethod
    def execute_wrapper(rebin_to_dimensions_radio=None,
                        shape_x=None,
                        shape_y=None,
                        rebin_by_factor_radio=None,
                        factor=None,
                        mode_field=None):
        if rebin_to_dimensions_radio.isChecked():
            params = (shape_x.value(), shape_y.value())
        elif rebin_by_factor_radio.isChecked():
            params = factor.value()
        else:
            raise ValueError('Unknown bin dimension mode')

        return partial(RebinFilter.filter_func, mode=mode_field.currentText(), rebin_param=params)


def modes():
    return ["constant", "edge", "wrap", "reflect", "symmetric"]


def _execute_par(data: numpy.ndarray, resized_data, mode, cores=None, chunksize=None, progress=None):
    f = ptsm.create_partial(skimage.transform.resize,
                            ptsm.return_to_second_but_dont_use_it,
                            mode=mode,
                            output_shape=resized_data.shape[1:])
    ptsm.execute(data, resized_data, f, cores, chunksize, progress=progress, msg="Applying Rebin")
    return resized_data


def _create_reshaped_array(images, rebin_param):
    old_shape = images.data.shape
    num_images = old_shape[0]

    # use SciPy's calculation to find the expected dimensions
    # int to avoid visible deprecation warning
    if isinstance(rebin_param, tuple):
        expected_dimy = int(rebin_param[0])
        expected_dimx = int(rebin_param[1])
    else:
        expected_dimy = int(rebin_param * old_shape[1])
        expected_dimx = int(rebin_param * old_shape[2])

    # allocate memory for images with new dimensions
    shape = (num_images, expected_dimy, expected_dimx)
    return pu.allocate_output(images, shape)
