from __future__ import (absolute_import, division, print_function)
import helper as h
from core.tools import importer


def cli_register(parser):
    parser.add_argument(
        "-log",
        "--minus-log",
        required=False,
        action='store_true',
        help="Calculate the -log of the sample data.")

    return parser


def gui_register(main_window):
    from core.algorithms import gui_compile_ui as gcu
    from gui.algorithm_dialog import AlgorithmDialog
    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle("Minus Log")

    def decorate_execute():
        return execute

    # replace dialog function with this one
    dialog.decorate_execute = decorate_execute
    return dialog


def execute(data, minus_log=True):
    """
    This filter should be used on transmission images (background corrected images).
    It converts the images from transmission to attenuation.

    :param data: Sample data which is to be processed. Expected in radiograms
    :param minus_log: Default True
                      Specify whether to calculate minus log or just return.
    """
    if minus_log:
        # import early to check if tomopy is available
        tomopy = importer.do_importing('tomopy')
        h.pstart("Calculating -log on the sample data.")
        # this check prevents division by 0 errors from the minus_log
        data[data == 0] = 1e-6
        # the operation is done in place
        tomopy.prep.normalize.minus_log(data, out=data)
        h.pstop("Finished calculating -log on the sample data.")

    return data
