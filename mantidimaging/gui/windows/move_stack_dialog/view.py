# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import uuid
from typing import Dict

from PyQt5.QtWidgets import QLabel, QComboBox

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.move_stack_dialog.presenter import MoveStackPresenter, Notification

STRICT_DATASET_ATTRS = ["Sample", "Flat Before", "Flat After", "Dark Before", "Dark After", "Recon"]


class MoveStackDialog(BaseDialogView):

    originDatasetName: QLabel
    originDataType: QLabel

    destinationNameComboBox: QComboBox
    destinationTypeComboBox: QComboBox

    def __init__(self, parent, origin_dataset_id: uuid.UUID, stack_id: uuid.UUID, origin_dataset_name: str,
                 origin_data_type: str, is_dataset_strict: Dict[str, bool]):
        super().__init__(parent, 'gui/ui/move_stack_dialog.ui')

        self.originDatasetName.setText(origin_dataset_name)
        self.originDataType.setText(origin_data_type)
        self._origin_dataset_id = origin_dataset_id
        self.destination_dataset_info = is_dataset_strict
        self._stack_id = stack_id

        self.parent_view = parent
        self.presenter = MoveStackPresenter(self)

        self.destinationNameComboBox.addItems([name for name in is_dataset_strict.keys()])
        self._destination_dataset_is_strict = is_dataset_strict[self.destinationNameComboBox.currentText()]

        self.destinationNameComboBox.currentIndexChanged.connect(self._on_destination_dataset_changed)
        self._create_destination_type_options(self._destination_dataset_is_strict)

    def _create_destination_type_options(self, destination_dataset_is_strict: bool):
        """
        Create optional data types for the destination depending on where the destination dataset is strict or mixed.
        :param destination_dataset_is_strict: Whether the destination dataset is strict.
        """
        if destination_dataset_is_strict:
            if self.destinationNameComboBox.currentText() == self.originDatasetName.text():
                self.destinationTypeComboBox.addItems(set(STRICT_DATASET_ATTRS) - {self.originDataType.text()})
            else:
                self.destinationTypeComboBox.addItems(STRICT_DATASET_ATTRS)
        else:
            self.destinationTypeComboBox.addItems(["Images", "Recon"])

    def accept(self):
        self.presenter.notify(Notification.ACCEPTED)
        self.close()

    def _on_destination_dataset_changed(self):
        """
        Check if the new dataset selection is strict or mixed and change the data type accordingly.
        """
        selected_dataset_is_strict = self.destination_dataset_info[self.destinationNameComboBox.currentText()]
        self.destinationTypeComboBox.clear()
        self._create_destination_type_options(selected_dataset_is_strict)
        self._destination_dataset_is_strict = selected_dataset_is_strict

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
    def destination_dataset_name(self) -> str:
        return self.destinationNameComboBox.currentText()
