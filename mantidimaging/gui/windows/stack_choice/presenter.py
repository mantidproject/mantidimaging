# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import traceback
from typing import TYPE_CHECKING, List, Optional, Tuple, Union
from uuid import UUID

from mantidimaging.core.data.images import Images
from mantidimaging.gui.windows.stack_choice.presenter_base import StackChoicePresenterMixin
from mantidimaging.gui.windows.stack_choice.view import Notification, StackChoiceView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.operations.presenter import FiltersWindowPresenter  # pragma: no cover


def _get_stack_from_uuid(original_stack, stack_uuid):
    for stack, uuid in original_stack:
        if uuid == stack_uuid:
            return stack
    raise RuntimeError("No useful stacks passed to Stack Choice Presenter")


class StackChoicePresenter(StackChoicePresenterMixin):
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
            else:
                super().notify(signal)
        except Exception as e:
            self.show_error(e, traceback.format_exc())

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
        self.operations_presenter.main_window.presenter.set_images_in_stack(self.stack_uuid, self.stack)
        self._clean_up_original_images_stack()
        self.view.choice_made = True
        self.close_view()

    def do_clean_up_original_data(self):
        self._clean_up_original_images_stack()
        self.view.choice_made = True
        self.close_view()

    def close_view(self):
        self.view.close()
        self.stack = None
        self.done = True

    def enable_nonpositive_check(self):
        self.view.original_stack.enable_nonpositive_check()
        self.view.new_stack.enable_nonpositive_check()
