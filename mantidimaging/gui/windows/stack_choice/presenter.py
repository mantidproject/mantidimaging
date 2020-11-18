# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from mantidimaging.core.data.images import Images
import traceback
from logging import getLogger
from typing import List, Optional, TYPE_CHECKING, Tuple, Union
from uuid import UUID

from mantidimaging.gui.windows.stack_choice.view import StackChoiceView, Notification

if TYPE_CHECKING:
    from mantidimaging.gui.windows.operations.presenter import FiltersWindowPresenter


def _get_stack_from_uuid(original_stack, stack_uuid):
    for stack, uuid in original_stack:
        if uuid == stack_uuid:
            return stack
    raise RuntimeError("No useful stacks passed to Stack Choice Presenter")


class StackChoicePresenter:
    def __init__(self,
                 original_stack: Union[List[Tuple[Images, UUID]], Images],
                 new_stack: Images,
                 operations_presenter: 'FiltersWindowPresenter',
                 stack_uuid: Optional[UUID],
                 view: Optional[StackChoiceView] = None):
        self.operations_presenter = operations_presenter

        if view is None:
            # Check if multiple stacks to choose from
            if isinstance(original_stack, list):
                self.stack = _get_stack_from_uuid(original_stack, stack_uuid)
            else:
                self.stack = original_stack
            view = StackChoiceView(self.stack, new_stack, self, parent=operations_presenter.view)

        self.view = view
        self.stack_uuid = stack_uuid
        self.done = False
        self.use_new_data = False

    def show(self):
        self.view.show()

    def notify(self, signal):
        try:
            if signal == Notification.CHOOSE_ORIGINAL:
                self.do_reapply_original_data()
            elif signal == Notification.CHOOSE_NEW_DATA:
                self.do_clean_up_original_data()
                self.use_new_data = True

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
