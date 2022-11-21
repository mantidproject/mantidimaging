# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from typing import Dict, NamedTuple

from PyQt5.QtWidgets import QLabel, QComboBox

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.move_stack_dialog.presenter import MoveStackPresenter, Notification


class MoveStackDialog(BaseDialogView):

    originDatasetName: QLabel
    originDataType: QLabel

    destinationNameComboBox: QComboBox
    destinationTypeComboBox: QComboBox

    def __init__(self, parent, origin_dataset_id: uuid.UUID, origin_dataset_name: str, origin_data_type: str,
                 destination_datasets: Dict[NamedTuple]):
        super().__init__(parent, 'gui/ui/move_stack_dialog.ui')

        self.originDatasetName.setText(origin_dataset_name)
        self.originDataType.setText(origin_data_type)
        self._origin_dataset_id = origin_dataset_id
        self.destination_dataset_info = destination_datasets

        self.parent_view = parent
        self.presenter = MoveStackPresenter(self)

        self.destinationNameComboBox.addItems([item.name for item in destination_datasets.values()])
        self._destination_dataset_is_strict = destination_datasets[self.destinationTypeComboBox.currentText()].is_strict

    def _on_accepted(self):
        self.presenter.notify(Notification.ACCEPTED)

    def _on_destination_dataset_change(self):
        selected_dataset_is_strict = self.destination_dataset_info[self.destinationTypeComboBox.currentText()].is_strict
        if selected_dataset_is_strict == self._destination_dataset_is_strict:
            return

        self.destinationTypeComboBox.clear()
        if selected_dataset_is_strict:
            self.destinationTypeComboBox.addItems(
                ["Sample", "Flat Before", "Flat After", "Dark Before", "Dark After", "Recon"])
        else:
            self.destinationTypeComboBox.addItems(["Images", "Recon"])

        self._destination_dataset_is_strict = selected_dataset_is_strict
