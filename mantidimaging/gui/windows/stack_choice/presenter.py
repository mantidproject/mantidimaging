import traceback
from logging import getLogger

from mantidimaging.gui.windows.stack_choice.view import StackChoiceView, Notification


def _get_stack_from_uuid(original_stack, stack_uuid):
    for stack, uuid in original_stack:
        if uuid == stack_uuid:
            return stack
    raise RuntimeError("No useful stacks passed to Stack Choice Presenter")


class StackChoicePresenter:
    def __init__(self, original_stack, new_stack, operations_presenter, stack_uuid, view=None):
        self.operations_presenter = operations_presenter

        if view is None:
            # Check if multiple stacks to choose from
            if isinstance(original_stack, list):
                self.stack = _get_stack_from_uuid(original_stack, stack_uuid)
            else:
                self.stack = original_stack
            view = StackChoiceView(self.stack, new_stack, self)

        self.view = view
        self.stack_uuid = stack_uuid
        self.done = False

    def show(self):
        self.view.show()

    def notify(self, signal):
        try:
            if signal == Notification.CHOOSE_ORIGINAL:
                self.do_reapply_original_data()
            elif signal == Notification.CHOOSE_NEW_DATA:
                self.do_clean_up_original_data()

        except Exception as e:
            self.operations_presenter.show_error(e, traceback.format_exc())
            getLogger(__name__).exception("Notification handler failed")

    def _clean_up_original_images_stack(self):
        if isinstance(self.operations_presenter.original_images_stack, list) \
                and len(self.operations_presenter.original_images_stack) > 1:
            for index, (_, uuid) in enumerate(self.operations_presenter.original_images_stack):
                if uuid == self.stack_uuid:
                    self.operations_presenter.original_images_stack.pop(index)
                    break
        else:
            self.operations_presenter.original_images_stack = None

    def do_reapply_original_data(self):
        self.operations_presenter.main_window.presenter.model.set_images_in_stack(self.stack_uuid, self.stack)
        self._clean_up_original_images_stack()
        self.view.choice_made = True
        self.close_view()

    def do_clean_up_original_data(self):
        self._clean_up_original_images_stack()
        self.stack.free_memory()
        self.view.choice_made = True
        self.close_view()

    def close_view(self):
        self.view.close()
        self.done = True
