# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import uuid

from PyQt5.QtWidgets import QLabel, QComboBox
from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.move_stack_dialog.presenter import MoveStackPresenter, Notification


class MoveStackDialog(BaseDialogView):

    originDatasetName: QLabel
    originDataType: QLabel

    destinationTypeComboBox: QComboBox

    def __init__(self, parent, origin_dataset_id: uuid.UUID, stack_id: uuid.UUID, origin_dataset_name: str,
                 origin_data_type: str):
        super().__init__(parent, 'gui/ui/move_stack_dialog.ui')

        self.originDatasetName.setText(origin_dataset_name)
        self.originDataType.setText(origin_data_type)
        self._origin_dataset_id = origin_dataset_id
        self._stack_id = stack_id

        self.parent_view = parent
        self.presenter = MoveStackPresenter(self)

        self.datasetSelector = DatasetSelectorWidgetView(self)
        self.layout().addWidget(self.datasetSelector, 3, 1)

        self.datasetSelector.currentIndexChanged.connect(self._on_destination_dataset_changed)
        self.datasetSelector.subscribe_to_main_window(parent)
        self._on_destination_dataset_changed()

    def accept(self):
        self.presenter.notify(Notification.ACCEPTED)
        self.close()

    def _on_destination_dataset_changed(self):
        self.presenter.notify(Notification.DATASET_CHANGED)

    @property
    def origin_dataset_id(self) -> uuid.UUID:
        return self._origin_dataset_id

    @property
    def stack_id(self) -> uuid.UUID:
        return self._stack_id

    @property
    def destination_stack_type(self) -> str:
        return self.destinationTypeComboBox.currentText()

    @property
    def destination_dataset_id(self) -> uuid.UUID:
        return self.datasetSelector.current()  # type: ignore
