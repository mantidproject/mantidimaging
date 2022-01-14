# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import List, TYPE_CHECKING, Iterable, Any, Dict

from mantidimaging.core.data import Images
from mantidimaging.core.operation_history import const
from mantidimaging.core.operation_history.operations import ImageOperation, deserialize_metadata
from mantidimaging.gui.mvp_base import BasePresenter
from .model import OpHistoryCopyDialogModel
from ...utility.common import operation_in_progress

if TYPE_CHECKING:
    from mantidimaging.gui.dialogs.op_history_copy import OpHistoryCopyDialogView  # pragma: no cover
    from mantidimaging.gui.windows.main import MainWindowView  # pragma: no cover


class OpHistoryCopyDialogPresenter(BasePresenter):
    operations: List[ImageOperation]
    main_window: 'MainWindowView'
    view: 'OpHistoryCopyDialogView'

    def __init__(self, view, images: Images, main_window):
        super().__init__(view)
        self.view = view
        self.model = OpHistoryCopyDialogModel(images)
        self.main_window = main_window
        self.operations = []

    def set_target_stack(self, uuid):
        self.model.images = self.main_window.get_stack_visualiser(uuid).presenter.images

    def set_source_stack(self, uuid):
        history_to_apply = self.main_window.get_stack_history(uuid)
        self.operations = deserialize_metadata(history_to_apply)
        self.display_op_history()

    def display_op_history(self):
        self.view.display_op_history(self.operations)

    def do_selected_ops_changed(self):
        # TODO: previews
        pass

    def do_apply_ops(self):
        selected_ops = [op for op, selected in zip(self.operations, self.view.selected_op_indices) if selected]
        with operation_in_progress(f"{'Copying and ' if self.view.copy else ' '}Applying operations", '', self.view):
            result = self.model.apply_ops(selected_ops, self.view.copy)
            history = self.history_with_new_ops(selected_ops)
            result.metadata = history
        if self.view.copy:
            self.main_window.create_new_stack(result)

    def history_with_new_ops(self, applied_ops: Iterable[ImageOperation]) -> Dict[str, Any]:
        history = self.model.images.metadata.copy() if self.model.images.metadata else {}
        if const.OPERATION_HISTORY not in history:
            history[const.OPERATION_HISTORY] = []

        for op in applied_ops:
            history[const.OPERATION_HISTORY].append(op.serialize())

        return history
