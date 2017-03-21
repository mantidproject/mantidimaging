from __future__ import (absolute_import, division, print_function)
from PyQt4 import uic, QtCore
from PyQt4.QtGui import QMainWindow, QApplication


class ApplicationWindow(QMainWindow):
    def __init__(self, config):
        super(ApplicationWindow, self).__init__()
        uic.loadUi('./gui/ui/main_window.ui', self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("imgpy")
        from gui.stack_visualiser import StackVisualiser
        import numpy as np
        from imgdata import loader
        stack = loader.load_data(config)
        self.stack = StackVisualiser(self, stack)
        self.horizontalLayout.addWidget(self.stack)


def execute(config):
    import sys

    # create the GUI event loop
    qApp = QApplication(sys.argv)
    aw = ApplicationWindow(config)
    aw.show()

    return sys.exit(qApp.exec_())
