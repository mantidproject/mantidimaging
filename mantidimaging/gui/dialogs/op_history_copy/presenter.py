from enum import Enum
from typing import List

from mantidimaging.core.data import Images
from mantidimaging.core.operation_history import const
from mantidimaging.core.operation_history.operations import ImageOperation, deserialize_metadata
from mantidimaging.gui.mvp_base import BasePresenter
from .model import OpHistoryCopyDialogModel


class Notification(Enum):
    SELECTED_OPS_CHANGED = 0
    APPLY_OPS = 1


class OpHistoryCopyDialogPresenter(BasePresenter):
    operations: List[ImageOperation]

    def __init__(self, view, images: Images, main_window):
        super(OpHistoryCopyDialogPresenter, self).__init__(view)
        self.model = OpHistoryCopyDialogModel(images)
        self.main_window = main_window
        self.operations = []

    def notify(self, signal: Notification):
        if signal == Notification.SELECTED_OPS_CHANGED:
            self.selected_ops_changed()
        elif signal == Notification.APPLY_OPS:
            self.apply_ops()

    def set_stack_uuid(self, uuid):
        history_to_apply = self.main_window.get_stack_history(uuid)
        self.operations = deserialize_metadata(history_to_apply)
        self.display_op_history()

    def display_op_history(self):
        self.view.display_op_history(self.operations)

    def selected_ops_changed(self):
        # TODO: previews
        pass

    def apply_ops(self):
        selected_ops = [op for op, selected in zip(self.operations, self.view.selected_op_indices) if selected]
        result = self.model.apply_ops(selected_ops)

        # Copy history and append new operations
        history = self.model.images.metadata.copy()
        for op in selected_ops:
            history[const.OPERATION_HISTORY].append(op.serialize())

        self.main_window.create_new_stack(Images(result, metadata=history), "A result")
