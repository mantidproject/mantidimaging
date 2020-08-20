from functools import partial

from mantidimaging.core.data import Images

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.tools import importer
from mantidimaging.core.utility.progress_reporting import Progress


class MinusLogFilter(BaseFilter):
    filter_name = "Minus Log"

    @staticmethod
    def filter_func(images: Images, minus_log=True, progress=None):
        """
        This filter should be used on transmission images (background corrected
        images).

        It converts the images from transmission to attenuation.

        :param images: Sample data which is to be processed. Expected in radiograms
        :param minus_log: Specify whether to calculate minus log or just return.

        :return: Inverted image
        """
        progress = Progress.ensure_instance(progress, task_name='Minus Log')

        if minus_log:
            # import early to check if tomopy is available
            tomopy = importer.do_importing('tomopy')

            with progress:
                progress.update(msg="Calculating -log on the sample data")
                sample = images.data
                # this check prevents division by 0 errors from the minus_log
                sample[sample == 0] = 1e-6

                # the operation is done in place
                tomopy.prep.normalize.minus_log(sample, out=sample)

        return images

    @staticmethod
    def execute_wrapper(**kwargs):
        return partial(MinusLogFilter.filter_func, minus_log=True)

    @staticmethod
    def register_gui(form, on_change, view):
        # Not much here, this filter does one thing and one thing only.
        return {}
