# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import Iterable, Tuple

from PyQt5.QtWidgets import QCheckBox, QLabel, QGroupBox, QWidget, QSizePolicy, QPushButton, QVBoxLayout

from mantidimaging.core.operation_history.operations import ImageOperation
from mantidimaging.gui.mvp_base import BaseDialogView
from .presenter import OpHistoryCopyDialogPresenter


class OpHistoryCopyDialogView(BaseDialogView):
    operationsContainer: QGroupBox
    _copy: QCheckBox
    applyButton: QPushButton
    previewsLayout: QVBoxLayout

    def __init__(self, parent, images, main_window):
        super().__init__(parent, "gui/ui/op_history_copy_dialog.ui")
        self.presenter = OpHistoryCopyDialogPresenter(self, images, main_window)

        self.stackTargetSelector.stack_selected_uuid.connect(self.presenter.set_target_stack)
        self.stackSourceSelector.stack_selected_uuid.connect(self.presenter.set_source_stack)
        self.stackSourceSelector.subscribe_to_main_window(main_window)
        self.stackTargetSelector.subscribe_to_main_window(main_window)
        # self.previews = FilterPreviews()
        # self.previewsLayout.addWidget(self.previews)
        self.applyButton.clicked.connect(lambda: self.presenter.do_apply_ops())

    def display_op_history(self, operations: Iterable[ImageOperation]):
        layout = self.operationsContainer.layout()
        while layout.count():
            layout.takeAt(0)

        for op in operations:
            row, check = self.build_operation_row(op)
            check.stateChanged.connect(lambda: self.presenter.do_selected_ops_changed())
            layout.addWidget(row)

    @staticmethod
    def build_operation_row(operation: ImageOperation) -> Tuple[QWidget, QCheckBox]:
        parent = QWidget()
        parent_layout = QVBoxLayout(parent)
        # parent_layout = QGridLayout(parent)
        parent.setLayout(parent_layout)

        check = QCheckBox(parent)
        check.setText(operation.display_name)
        check.setStyleSheet('font-weight: bold')
        check.setChecked(True)
        check.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Preferred)
        parent_layout.addWidget(check)

        row_num = 1
        for k, v in operation.filter_kwargs.items():
            parent_layout.addWidget(QLabel(f"{k}: {v}"))
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

    @property
    def copy(self) -> bool:
        return self._copy.isChecked()
