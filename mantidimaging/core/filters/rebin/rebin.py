from functools import partial
from typing import Optional

import numpy
import skimage.transform

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import exclusive_mem as pem
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility import add_property_to_form


class RebinFilter(BaseFilter):
    """
    This filter temporarily increases memory usage, while the image is being rebinned.
    The memory usage will be lowered after the filter has finished executing.
    """
    filter_name = "Rebin"

    @staticmethod
    def filter_func(data: Images, rebin_param=0.5, mode=None, cores=None, chunksize=None, progress=None) -> Images:
        """
        :param data: Sample data which is to be processed. Expects radiograms
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
        h.check_data_stack(data)

        if isinstance(rebin_param, tuple):
            param_valid = rebin_param[0] > 0 and rebin_param[1] > 0
        else:
            param_valid = rebin_param > 0

        if param_valid:
            sample = data.sample
            if data.sample_memory_file_name is not None:
                sample_name = data.sample_memory_file_name
                data.free_sample()
            else:
                sample_name = None
            empty_resized_data = _create_reshaped_array(sample.shape, sample.dtype, rebin_param, sample_name)
            progress = Progress.ensure_instance(progress, num_steps=sample.shape[0], task_name='Rebin')
            if pu.multiprocessing_necessary(sample.shape, cores) and sample_name is not None:
                rebinned = _execute_par(sample, empty_resized_data, mode, cores, chunksize, progress)
            else:
                rebinned = _execute_seq(sample, empty_resized_data, mode, progress)
            data.sample = rebinned

        return data

    @staticmethod
    def register_gui(form, on_change, view):
        # Rebin by uniform factor options
        _, factor = add_property_to_form('Factor', 'float', 0.5, (0.0, 1.0), on_change=on_change)
        factor.setSingleStep(0.05)

        # Rebin to target shape options
        shape_range = (0, 9999)

        _, shape_x = add_property_to_form('X', 'int', valid_values=shape_range, on_change=on_change)
        _, shape_y = add_property_to_form('Y', 'int', valid_values=shape_range, on_change=on_change)

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
    with progress:
        progress.update(msg="Applying rebin.")
        f = pem.create_partial(skimage.transform.resize, mode=mode, output_shape=resized_data.shape[1:])
        resized_data = pem.execute(data, f, cores, chunksize, "Rebin", output_data=resized_data, progress=progress)
    return resized_data


def _execute_seq(data: numpy.ndarray, resized_data, mode, progress=None):
    with progress:
        progress.update(msg="Starting image rebinning.")

        num_images = resized_data.shape[0]
        progress.set_estimated_steps(num_images)

        for idx in range(num_images):
            resized_data[idx] = skimage.transform.resize(data[idx], resized_data.shape[1:], mode=mode)
            progress.update()

    return resized_data


def _create_reshaped_array(old_shape, dtype, rebin_param, sample_name: Optional[str]):
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
    data = pu.create_array(sample_name, shape, dtype)

    return data
