from functools import partial

from mantidimaging import helper as h
from mantidimaging.core.data import Images
from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.utility.optional_imports import safe_import
from mantidimaging.core.utility.progress_reporting import Progress


class RingRemovalFilter(BaseFilter):
    filter_name = "Ring Removal"

    @staticmethod
    def filter_func(data: Images,
                    run_ring_removal=False,
                    center_x=None,
                    center_y=None,
                    thresh=300.0,
                    thresh_max=300.0,
                    thresh_min=-100.0,
                    theta_min=30,
                    rwidth=30,
                    cores=None,
                    chunksize=None,
                    progress=None):
        """
        Removal of ring artifacts in reconstructed volume.

        :param data: Sample data which is to be processed. Expected in radiograms
        :param run_ring_removal: Uses Wavelet-Fourier based ring removal
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

        if run_ring_removal:
            h.check_data_stack(data)

            with progress:
                progress.update(msg="Ring Removal")
                sample = data.sample
                tp.remove_ring(data.sample,
                               center_x=center_x,
                               center_y=center_y,
                               thresh=thresh,
                               thresh_max=thresh_max,
                               thresh_min=thresh_min,
                               theta_min=theta_min,
                               rwidth=rwidth,
                               ncore=cores,
                               nchunk=chunksize,
                               out=sample)

        return data

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        range1 = (0, 1000000)
        range2 = (-1000000, 1000000)

        _, x_field = add_property_to_form('Abcissa X', 'int', valid_values=range1, form=form, on_change=on_change)

        _, y_field = add_property_to_form('Ordinate Y', 'int', valid_values=range1, form=form, on_change=on_change)

        _, thresh = add_property_to_form('Threshold', 'float', valid_values=range2, form=form, on_change=on_change)

        _, thresh_min = add_property_to_form('Threshold Min',
                                             'float',
                                             valid_values=range2,
                                             form=form,
                                             on_change=on_change)

        _, thresh_max = add_property_to_form('Threshold Max',
                                             'float',
                                             valid_values=range2,
                                             form=form,
                                             on_change=on_change)

        _, theta = add_property_to_form('Theta', 'int', valid_values=(-1000, 1000), form=form, on_change=on_change)

        _, rwidth = add_property_to_form('RWidth', 'int', valid_values=range2, form=form, on_change=on_change)

        return {
            "x_field": x_field,
            "y_field": y_field,
            "thresh": thresh,
            "thresh_min": thresh_min,
            "thresh_max": thresh_max,
            "theta": theta,
            "rwidth": rwidth,
        }

    @staticmethod
    def execute_wrapper(x_field=None,
                        y_field=None,
                        thresh=None,
                        thresh_max=None,
                        thresh_min=None,
                        theta=None,
                        rwidth=None):
        return partial(RingRemovalFilter.filter_func,
                       run_ring_removal=True,
                       center_x=x_field,
                       center_y=y_field,
                       thresh=thresh,
                       thresh_max=thresh_max,
                       thresh_min=thresh_min,
                       theta_min=theta,
                       rwidth=rwidth)
