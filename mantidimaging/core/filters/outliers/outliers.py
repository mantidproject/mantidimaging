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
DIM_2D = "2D"
DIM_1D = "1D"
_default_dim = DIM_2D


class OutliersFilter(BaseFilter):
    filter_name = "Remove Outliers TomoPy"

    @staticmethod
    def filter_func(data, diff=None, radius=_default_radius, mode=_default_mode, axis=0, type=_default_dim,
                    cores=None, progress=None):
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
        if not utility.multiprocessing_necessary(data.data.shape, cores):
            cores = 1

        if diff and radius and diff > 0 and radius > 0:
            with progress:
                progress.update(msg="Applying outliers with threshold: {0} and " "radius {1}".format(diff, radius))

                sample = data.data
                # By default tomopy only clears bright outliers.
                # As a workaround inverting the image makes the dark outliers the brightest
                if mode == OUTLIERS_DARK:
                    np.negative(sample, out=sample)

                tomopy = importer.do_importing('tomopy')
                if type == "2D":
                    tomopy.misc.corr.remove_outlier(sample, diff, radius, axis, ncore=cores, out=sample)
                else:
                    tomopy.misc.corr.remove_outlier1d(sample, diff, radius, axis, ncore=cores, out=sample)
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
        _, axis_field = add_property_to_form('Axis', Type.INT, 0, (0, 2), form=form, on_change=on_change)

        _, dim_field = add_property_to_form('Dims', Type.CHOICE, valid_values=dims(), form=form,
                                            on_change=on_change)

        return {'diff_field': diff_field, 'size_field': size_field, 'mode_field': mode_field,
                'axis_field': axis_field, 'dim_field': dim_field}

    @staticmethod
    def execute_wrapper(diff_field=None, size_field=None, mode_field=None, axis_field=None, dim_field=None):
        return partial(OutliersFilter.filter_func,
                       diff=diff_field.value(),
                       radius=size_field.value(),
                       mode=mode_field.currentText(),
                       axis=axis_field.value(),
                       type=dim_field.currentText())


def modes():
    return [OUTLIERS_BRIGHT, OUTLIERS_DARK]


def dims():
    return [DIM_2D, DIM_1D]
