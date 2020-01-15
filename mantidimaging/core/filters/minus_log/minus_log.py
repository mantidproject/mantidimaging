from functools import partial

from mantidimaging.core.filters.base_filter import BaseFilter
from mantidimaging.core.tools import importer
from mantidimaging.core.utility.progress_reporting import Progress


class MinusLogFilter(BaseFilter):
    filter_name = "Minus Log"

    @staticmethod
    def _filter_func(data, minus_log=True, progress=None):
        """
        This filter should be used on transmission images (background corrected
        images).

        It converts the images from transmission to attenuation.

        :param data: Sample data which is to be processed. Expected in radiograms
        :param minus_log: Specify whether to calculate minus log or just return.

        :return: Inverted image
        """
        progress = Progress.ensure_instance(progress,
                                            task_name='Minus Log')

        if minus_log:
            # import early to check if tomopy is available
            tomopy = importer.do_importing('tomopy')

            with progress:
                progress.update(msg="Calculating -log on the sample data")

                # this check prevents division by 0 errors from the minus_log
                data[data == 0] = 1e-6

                # the operation is done in place
                tomopy.prep.normalize.minus_log(data, out=data)

        return data

    @staticmethod
    def execute_wrapper(**kwargs):
        return partial(MinusLogFilter._filter_func, minus_log=True)

    @staticmethod
    def register_gui(form, on_change):
        # Not much here, this filter does one thing and one thing only.
        return {}


def _cli_register(parser):
    parser.add_argument(
        "-log",
        "--minus-log",
        required=False,
        action='store_true',
        help="Calculate the -log of the sample data.")

    return parser
