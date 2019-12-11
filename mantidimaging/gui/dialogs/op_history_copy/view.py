from typing import Iterable, Tuple

from PyQt5.QtWidgets import QCheckBox, QLabel, QGroupBox, QWidget, QSizePolicy, QGridLayout

from mantidimaging.core.operation_history.operations import ImageOperation
from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.filters.filter_previews import FilterPreviews
from .presenter import OpHistoryCopyDialogPresenter, Notification


class OpHistoryCopyDialogView(BaseDialogView):
    operationsContainer: QGroupBox

    def __init__(self, parent, images, main_window):
        super(OpHistoryCopyDialogView, self).__init__(parent, "gui/ui/op_history_copy_dialog.ui")
        self.presenter = OpHistoryCopyDialogPresenter(self, images, main_window)
        self.stackTargetSelector.stack_selected_uuid.connect(self.presenter.set_target_stack)
        self.stackSourceSelector.stack_selected_uuid.connect(self.presenter.set_source_stack)
        self.stackSourceSelector.subscribe_to_main_window(main_window)
        self.stackTargetSelector.subscribe_to_main_window(main_window)
        self.previews = FilterPreviews()
        self.previewsLayout.addWidget(self.previews)
        self.applyButton.clicked.connect(lambda: self.presenter.notify(Notification.APPLY_OPS))

    def display_op_history(self, operations: Iterable[ImageOperation]):
        layout = self.operationsContainer.layout()
        while layout.count():
            row = layout.takeAt(0)
            if row.widget():
                row.widget().deleteLater()

        for op in operations:
            row, check = self.build_operation_row(op)
            check.stateChanged.connect(lambda: self.presenter.notify(Notification.SELECTED_OPS_CHANGED))
            layout.addWidget(row)

    @staticmethod
    def build_operation_row(operation: ImageOperation) -> Tuple[QWidget, QCheckBox]:
        parent = QWidget()
        parent_layout = QGridLayout(parent)
        parent.setLayout(parent_layout)

        check = QCheckBox(parent=parent, checked=True)
        check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        parent_layout.addWidget(check, 0, 0)

        op_name_label = QLabel(operation.display_name)
        op_name_label.setStyleSheet('font-weight: bold')
        parent_layout.addWidget(op_name_label, 0, 1)
        row_num = 1
        for arg in operation.filter_args:
            parent_layout.addWidget(QLabel(arg), row_num, 1)
            row_num += 1

        for k, v in operation.filter_kwargs.items():
            parent_layout.addWidget(QLabel(f"{k}: {v}"), row_num, 1)
            row_num += 1

        return parent, check

    @property
    def selected_op_indices(self):
        check_states = []
        for row_num in range(self.operationsContainer.layout().count()):
            row = self.operationsContainer.layout().itemAt(row_num).widget()
            check = row.layout().itemAt(0).widget()
            check_states.append(check.isChecked())
        return check_states
