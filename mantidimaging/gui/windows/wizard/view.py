from PyQt5 import QtCore

from mantidimaging.gui.mvp_base import BaseMainWindowView


class WizardView(BaseMainWindowView):
    def __init__(self):
        super(WizardView, self).__init__(None, "gui/ui/wizard.ui")

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("Workflow Wizard")
