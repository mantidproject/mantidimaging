from __future__ import absolute_import, division, print_function

import sys

from PyQt5.Qt import QApplication

from mantidimaging.gui.main_window.mw_view import MainWindowView

from .filter_registration import gui_register


def execute(config):
    # create the GUI event loop
    q_application = QApplication(sys.argv)
    application_window = MainWindowView(config)

    # register gui part of algorithms into view
    gui_register(application_window.menuFilters,
                 'mantidimaging.core.filters',
                 ['mantidimaging.core.filters.wip'])

    application_window.show()

    return sys.exit(q_application.exec_())
