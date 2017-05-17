from __future__ import absolute_import, division, print_function

import sys

from core.algorithms import registrator
from PyQt4.QtGui import QApplication

from gui.main_window.mw_view import ImgpyMainWindowView


def execute(config):

    # create the GUI event loop
    qApp = QApplication(sys.argv)
    aw = ImgpyMainWindowView(config)
    # register gui stuff into view
    registrator.register_into(aw.menuFilters, func=registrator._gui)
    aw.show()

    return sys.exit(qApp.exec_())
