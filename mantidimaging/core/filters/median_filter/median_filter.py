from functools import partial
from logging import getLogger
from typing import Callable, Dict, Any, TYPE_CHECKING

import scipy.ndimage as scipy_ndimage

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.gpu import utility as gpu
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility import add_property_to_form

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout


class MedianFilter(BaseFilter):
    filter_name = "Median"

    @staticmethod
    def filter_func(data: Images, size=None, mode="reflect", cores=None, chunksize=None, progress=None, force_cpu=True):
        """
        :param data: Input data as a 3D numpy.ndarray
        :param size: Size of the kernel
        :param mode: The mode with which to handle the endges.
                     One of [reflect, constant, nearest, mirror, wrap].
        :param cores: The number of cores that will be used to process the data.
        :param chunksize: The number of chunks that each worker will receive.

        :return: Returns the processed data

        """
        h.check_data_stack(data)

        if size and size > 1:
            if not force_cpu:
                data = _execute_gpu(data.sample, size, mode, progress)
            elif pu.multiprocessing_necessary(data.sample.shape, cores):
                _execute_par(data.sample, size, mode, cores, chunksize, progress)
            else:
                _execute_seq(data.sample, size, mode, progress)

        h.check_data_stack(data)
        return data

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view) -> Dict[str, Any]:
        _, size_field = add_property_to_form('Kernel Size', 'int', 3, (0, 1000), form=form, on_change=on_change)

        _, mode_field = add_property_to_form('Mode', 'choice', valid_values=modes(), form=form, on_change=on_change)

        _, gpu_field = add_property_to_form('Use GPU',
                                            'bool',
                                            default_value=False,
                                            tooltip='Run the median filter on the GPU',
                                            form=form,
                                            on_change=on_change)

        return {'size_field': size_field, 'mode_field': mode_field, 'use_gpu_field': gpu_field}

    @staticmethod
    def execute_wrapper(size_field=None, mode_field=None, use_gpu_field=None):
        return partial(MedianFilter.filter_func,
                       size=size_field.value(),
                       mode=mode_field.currentText(),
                       force_cpu=not use_gpu_field.isChecked())


def modes():
    return ['reflect', 'constant', 'nearest', 'mirror', 'wrap']


def _execute_seq(data, size, mode, progress=None):
    log = getLogger(__name__)
    progress = Progress.ensure_instance(progress, num_steps=data.shape[0], task_name='Median filter')

    with progress:
        log.info("Median filter, with pixel data type: {0}, filter " "size/width: {1}.".format(data.dtype, size))

        progress.add_estimated_steps(data.shape[0])
        for idx in range(0, data.shape[0]):
            data[idx] = scipy_ndimage.median_filter(data[idx], size, mode=mode)
            progress.update()

    return data


def _execute_par(data, size, mode, cores=None, chunksize=None, progress=None):
    log = getLogger(__name__)
    progress = Progress.ensure_instance(progress, task_name='Median filter')

    # create the partial function to forward the parameters
    f = psm.create_partial(scipy_ndimage.median_filter, fwd_func=psm.return_fwd_func, size=size, mode=mode)

    with progress:
        log.info("PARALLEL median filter, with pixel data type: {0}, filter "
                 "size/width: {1}.".format(data.dtype, size))

        progress.update()
        data = psm.execute(data, f, cores, chunksize, "Median Filter", progress)

    return data


def _execute_gpu(data, size, mode, progress=None):
    log = getLogger(__name__)
    progress = Progress.ensure_instance(progress, num_steps=data.shape[0], task_name="Median filter GPU")
    cuda = gpu.CudaExecuter(data.dtype)

    with progress:
        log.info("GPU median filter, with pixel data type: {0}, filter " "size/width: {1}.".format(data.dtype, size))

        data = cuda.median_filter(data, size, mode, progress)

    return data
