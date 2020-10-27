import traceback
from logging import getLogger

from mantidimaging.gui.windows.stack_choice.view import StackChoiceView, Notification


class StackChoicePresenter:
    def __init__(self, original_stack, new_stack, operations_presenter, stack_uuid, view=None):
        if view is None:
            view = StackChoiceView(original_stack, new_stack, self)

        self.view = view
        self.operations_presenter = operations_presenter
        self.stack_uuid = stack_uuid

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

    def do_reapply_original_data(self):
        self.operations_presenter.main_window.model.set_stack(self.stack_uuid,
                                                              self.operations_presenter.original_images_stack)
        self.operations_presenter.original_images_stack = None
        self.close_view()

    def do_clean_up_original_data(self):
        self.operations_presenter.original_images_stack = None
        self.close_view()

    def close_view(self):
        self.view.close()
