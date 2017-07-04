from __future__ import absolute_import, division, print_function

import os
from functools import partial

from PyQt5 import Qt

from isis_imaging.core import io
from isis_imaging.core.algorithms import gui_compile_ui as gcu
from isis_imaging.core.algorithms import value_scaling
from isis_imaging.gui.algorithm_dialog import AlgorithmDialog
from isis_imaging.gui.main_window.load_dialog import select_file

from . import background_correction

GUI_MENU_NAME = 'Background Correction'


def _gui_register(main_window):

    dialog = AlgorithmDialog(main_window)
    gcu.execute("gui/ui/alg_dialog.ui", dialog)
    dialog.setWindowTitle(GUI_MENU_NAME)

    flatPath = Qt.QLineEdit()
    flatButton = Qt.QPushButton("Flat")
    flatButton.clicked.connect(lambda: select_file(flatPath, "Flat"))

    darkPath = Qt.QLineEdit()
    darkButton = Qt.QPushButton("Dark")
    darkButton.clicked.connect(lambda: select_file(darkPath, "Dark"))

    dialog.formLayout.addRow(flatPath, flatButton)
    dialog.formLayout.addRow(darkPath, darkButton)

    def decorate_execute():

        flat_path = str(flatPath.text())
        dark_path = str(darkPath.text())
        flat_extension = io.utility.get_file_extension(flat_path)
        dark_extension = io.utility.get_file_extension(dark_path)

        flat_dir = os.path.dirname(flat_path)
        dark_dir = os.path.dirname(dark_path)

        flat = (io.loader.load(flat_dir, in_format=flat_extension)).mean(axis=0)
        dark = (io.loader.load(dark_dir, in_format=dark_extension)).mean(axis=0)

        par = partial(background_correction.execute, flat=flat, dark=dark)

        # function to be applied before the execute function
        par.do_before = value_scaling.create_factors
        # function to be applied after the execute function
        par.do_after = value_scaling.apply_factor

        return par

    # replace dialog function with this one
    dialog.decorate_execute = decorate_execute
    return dialog
