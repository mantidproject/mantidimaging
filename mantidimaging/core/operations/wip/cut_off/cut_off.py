from functools import partial

import numpy as np

from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.utility.progress_reporting import Progress


class CutOffFilter(BaseFilter):
    filter_name = 'Intensity Cut Off'

    @staticmethod
    def filter_func(images, threshold=None, progress=None):
        """
        Cut off values above threshold relative to the max pixels.

        :param images: Input data as a 3D numpy.ndarray
        :param threshold: The threshold related to the minimum pixel value that
                          will be clipped
        :return: The processed 3D numpy.ndarray
        """
        progress = Progress.ensure_instance(progress, task_name='Cut Off')

        if threshold and threshold > 0.0:
            with progress:
                sample = images.data
                dmin = np.amin(sample)
                dmax = np.amax(sample)

                progress.update(msg=f"Applying cut-off with level: {threshold}, min value " f"{dmin}, max value {dmax}")

                rel_cut_off = dmin + threshold * (dmax - dmin)

                np.minimum(sample, rel_cut_off, out=sample)

        return images

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        _, threshold_field = add_property_to_form('Threshold',
                                                  'float',
                                                  0.95, (0.0, 1.0),
                                                  form=form,
                                                  on_change=on_change)
        threshold_field.setSingleStep(0.05)

        return {'threshold_field': threshold_field}

    @staticmethod
    def execute_wrapper(threshold_field):
        return partial(CutOffFilter.filter_func, threshold=threshold_field.value())
