from functools import partial

import numpy as np

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.parallel import utility
from mantidimaging.core.tools import importer
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.utility.qt_helpers import Type

OUTLIERS_DARK = 'dark'
OUTLIERS_BRIGHT = 'bright'
_default_radius = 3
_default_mode = OUTLIERS_BRIGHT


class OutliersFilter(BaseFilter):
    filter_name = "Remove Outliers"

    @staticmethod
    def filter_func(data, diff=None, radius=_default_radius, mode=_default_mode, cores=None, progress=None):
        """
        Requires tomopy to be available.

        :param data: Input data as a 3D numpy.ndarray
        :param diff: Pixel value difference above which to crop bright pixels
        :param radius: Size of the median filter to apply
        :param mode: Spot brightness to remove.
                     Either 'bright' or 'dark'.
        :param cores: The number of cores that will be used to process the data.

        :return: The processed 3D numpy.ndarray
        """
        progress = Progress.ensure_instance(progress, task_name='Outliers', num_steps=3)
        if not utility.multiprocessing_necessary(data.sample.shape, cores):
            cores = 1

        if diff and radius and diff > 0 and radius > 0:
            with progress:
                progress.update(msg="Applying outliers with threshold: {0} and " "radius {1}".format(diff, radius))

                # we flip the histogram horizontally, this makes the darkest pixels
                # the brightest
                sample = data.sample
                if mode == OUTLIERS_DARK:
                    np.negative(sample, out=sample)

                tomopy = importer.do_importing('tomopy')
                tomopy.misc.corr.remove_outlier(sample, diff, radius, ncore=cores, out=sample)
                progress.update()

                # reverse the inversion
                if mode == OUTLIERS_DARK:
                    np.negative(sample, out=sample)

        return data

    @staticmethod
    def register_gui(form, on_change, view):
        _, diff_field = add_property_to_form('Difference',
                                             'float',
                                             1,
                                             valid_values=(-1000000, 1000000),
                                             form=form,
                                             on_change=on_change)
        diff_field.setDecimals(7)

        _, size_field = add_property_to_form('Size', Type.INT, 3, (0, 1000), form=form, on_change=on_change)

        _, mode_field = add_property_to_form('Mode', Type.CHOICE, valid_values=modes(), form=form, on_change=on_change)

        return {'diff_field': diff_field, 'size_field': size_field, 'mode_field': mode_field}

    @staticmethod
    def execute_wrapper(diff_field=None, size_field=None, mode_field=None):
        return partial(OutliersFilter.filter_func,
                       diff=diff_field.value(),
                       radius=size_field.value(),
                       mode=mode_field.currentText())


def modes():
    return [OUTLIERS_BRIGHT, OUTLIERS_DARK]
