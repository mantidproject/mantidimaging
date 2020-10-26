from mantidimaging.gui.windows.wizard.model import WizardModel
from mantidimaging.gui.windows.wizard.view import WizardView


class WizardPresenter():
    def __init__(self, view=None, model=None):
        if view is None:
            view = WizardView()
        if model is None:
            model = WizardModel()

        self.view = view
        self.model = model

    def show(self):
        self.view.show()
