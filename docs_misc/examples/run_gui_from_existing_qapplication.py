import sys
from PyQt5 import Qt


class Window(Qt.QMainWindow):
    """
    Super simple main window that shows how the mantidimaging GUI can be shown
    form another QApplication.
    """
    def __init__(self):
        super(Window, self).__init__()

        # A button to launch the UI
        b = Qt.QPushButton("Run GUI", self)
        b.clicked.connect(self.run_mantidimagingimaging_gui)
        self.setCentralWidget(b)

        self.mi_window = None

    def run_mantidimagingimaging_gui(self):
        # Cache the main window (subsequent requests to show UI will be much faster)
        if self.mi_window is None:
            from mantidimaging.gui.main_window import MainWindowView
            mw = MainWindowView(None)

            # Replace the exit signal with hiding the window (keeps the
            # QApplication running)
            mw.actionExit.triggered.disconnect()
            mw.actionExit.triggered.connect(lambda: mw.hide())

        # Make the UI visible
        mw.show()


app = Qt.QApplication(sys.argv)
win = Window()
win.show()
app.exec_()
