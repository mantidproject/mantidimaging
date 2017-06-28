from __future__ import absolute_import, division, print_function

import sys

from isis_imaging.core.algorithms import registrator
from PyQt5.Qt import QApplication

from isis_imaging.gui.main_window.mw_view import MainWindowView


def execute(config):

    # create the GUI event loop
    qApp = QApplication(sys.argv)
    aw = MainWindowView(config)
    # register gui stuff into view
    registrator.register_into(aw.menuFilters, func=registrator._gui)
    aw.show()

    return sys.exit(qApp.exec_())
