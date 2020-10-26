from mantidimaging.gui.windows.stack_choice.model import StackChoiceModel
from mantidimaging.gui.windows.stack_choice.view import StackChoiceView


class StackChoicePresenter():
    def __init__(self, original_stack, new_stack, operations_presenter, view=None, model=None):
        if view is None:
            view = StackChoiceView(original_stack, new_stack)
        if model is None:
            model = StackChoiceModel()

        self.view = view
        self.model = model
        self.operations_presenter = operations_presenter

    def show(self):
        self.view.show()
