from typing import Iterable, Tuple

from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QGroupBox, QWidget

from mantidimaging.core.operation_history.operations import ImageOperation
from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.filters.filter_previews import FilterPreviews
from .presenter import OpHistoryCopyDialogPresenter, Notification


class OpHistoryCopyDialogView(BaseDialogView):
    operationsContainer: QGroupBox

    def __init__(self, parent, images, main_window):
        super(OpHistoryCopyDialogView, self).__init__(parent, "gui/ui/op_history_copy_dialog.ui")
        self.presenter = OpHistoryCopyDialogPresenter(self, images, main_window)
        self.stackSelector.stack_selected_uuid.connect(self.presenter.set_stack_uuid)
        self.stackSelector.subscribe_to_main_window(main_window)
        self.previews = FilterPreviews()
        self.previewsLayout.addWidget(self.previews)
        self.applyButton.clicked.connect(lambda: self.presenter.notify(Notification.APPLY_OPS))

        self.op_checks = []

    def display_op_history(self, operations: Iterable[ImageOperation]):
        # Clear the operations container
        self.op_checks = []
        layout = self.operationsContainer.layout()
        while layout.count():
            row = layout.takeAt(0)
            if row.widget():
                row.widget().deleteLater()

        for op in operations:
            row, check = self.build_operation_row(op)
            check.stateChanged.connect(lambda: self.presenter.notify(Notification.SELECTED_OPS_CHANGED))
            self.op_checks.append(check)
            layout.addWidget(row)

    def build_operation_row(self, operation: ImageOperation) -> Tuple[QWidget, QCheckBox]:
        # TODO: layout nicely
        parent = QWidget()
        layout = QHBoxLayout(parent)
        parent.setLayout(layout)

        check = QCheckBox(parent=parent, checked=True)
        layout.addWidget(check)
        layout.addWidget(QLabel(operation.friendly_name))

        return parent, check

    @property
    def selected_op_indices(self):
        check_states = []
        for row_num in range(self.operationsContainer.layout().count()):
            row = self.operationsContainer.layout().itemAt(row_num).widget()
            check = row.layout().itemAt(0).widget()
            check_states.append(check.isChecked())
        return check_states
