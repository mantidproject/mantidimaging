from __future__ import (absolute_import, division, print_function)
from PyQt4 import uic, QtCore
from PyQt4.QtGui import QMainWindow, QApplication


class ApplicationWindow(QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        uic.loadUi('./gui/ui/main_window.ui', self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("imgpy")
        from gui.stack_visualiser import StackVisualiser
        import numpy as np
        cube = np.random.rand(500, 2048, 2048)
        self.stack = StackVisualiser(self, cube)
        self.horizontalLayout.addWidget(self.stack)


if __name__ == '__main__':
    import sys

    # create the GUI event loop
    qApp = QApplication(sys.argv)
    aw = ApplicationWindow()
    aw.show()

    sys.exit(qApp.exec_())
