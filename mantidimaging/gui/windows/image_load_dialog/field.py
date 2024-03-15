# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from pathlib import Path

import numpy as np

from PyQt5.QtWidgets import QTreeWidgetItem, QWidget, QSpinBox, QTreeWidget, QHBoxLayout, QLabel, QCheckBox, QPushButton

from mantidimaging.core.utility import size_calculator
from mantidimaging.core.utility.data_containers import Indices, FILE_TYPES


class Field:
    _widget: QTreeWidgetItem
    _use: QCheckBox
    _spinbox_widget: QWidget | None = None
    _start_spinbox: QSpinBox | None = None
    _stop_spinbox: QSpinBox | None = None
    _increment_spinbox: QSpinBox | None = None
    _shape_widget: QTreeWidgetItem | None = None
    _tree: QTreeWidget
    _path: QTreeWidgetItem

    def __init__(self, tree: QTreeWidget, widget: QTreeWidgetItem, use: QCheckBox, select_button: QPushButton,
                 file_info: FILE_TYPES):
        self._tree = tree
        self._widget = widget
        self._use = use
        self._path = QTreeWidgetItem(self._widget)
        self._path.setText(0, "Path")
        self.select_button = select_button
        self.file_info = file_info

        if file_info == FILE_TYPES.SAMPLE:
            self._init_indices()

    def set_images(self, image_files: list[Path]) -> None:
        if len(image_files) > 0:
            self.path = image_files[0]
            self.update_shape(len(image_files))

    @property
    def widget(self) -> QTreeWidgetItem:
        """
        Returns the top-level widget of the section.
        All other fields are nested under it
        :return:
        """
        return self._widget

    @property
    def use(self) -> QCheckBox:
        return self._use

    @use.setter
    def use(self, value: bool) -> None:
        self._use.setChecked(value)

    @property
    def path_widget(self) -> QTreeWidgetItem:
        return self._path

    @property
    def path(self) -> Path | None:
        if path_text := self.path_widget.text(1):
            return Path(path_text)
        else:
            return None

    @path.setter
    def path(self, value: Path) -> None:
        if not isinstance(value, Path):
            raise RuntimeError(f"The object passed as path for this field is not a Path. Instead got {type(value)}")
        if value != "":
            self.path_widget.setText(1, str(value))
            self.widget.setText(1, value.name)
            self.use.setChecked(True)

    def _init_indices(self) -> None:
        indices_item = QTreeWidgetItem(self._widget)
        indices_item.setText(0, "File indices")
        _spinbox_layout = QHBoxLayout()

        self._start_spinbox = QSpinBox(self._tree.parent())
        _spinbox_layout.addWidget(QLabel("Start", self._tree.parent()))
        _spinbox_layout.addWidget(self._start_spinbox)

        self._stop_spinbox = QSpinBox(self._tree.parent())
        _spinbox_layout.addWidget(QLabel("Stop", self._tree.parent()))
        _spinbox_layout.addWidget(self._stop_spinbox)

        self._increment_spinbox = QSpinBox(self._tree.parent())
        self._increment_spinbox.setMinimum(1)
        _spinbox_layout.addWidget(QLabel("Increment", self._tree.parent()))
        _spinbox_layout.addWidget(self._increment_spinbox)

        self._spinbox_widget = QWidget(self._tree.parent())
        self._spinbox_widget.setLayout(_spinbox_layout)

        self._tree.setItemWidget(indices_item, 1, self._spinbox_widget)

    @property
    def _start(self) -> QSpinBox:
        if self._spinbox_widget is None:
            self._init_indices()
        # assert to clear up mypy error for wrong type
        assert self._start_spinbox is not None
        return self._start_spinbox

    @_start.setter
    def _start(self, value: int) -> None:
        self._start.setValue(value)

    @property
    def _stop(self) -> QSpinBox:
        if self._spinbox_widget is None:
            self._init_indices()
        # assert to clear up mypy error for wrong type
        assert self._stop_spinbox is not None
        return self._stop_spinbox

    @_stop.setter
    def _stop(self, value: int) -> None:
        self._stop.setValue(value)

    @property
    def _increment(self) -> QSpinBox:
        if self._spinbox_widget is None:
            self._init_indices()
        # assert to clear up mypy error for wrong type
        assert self._increment_spinbox is not None
        return self._increment_spinbox

    @_increment.setter
    def _increment(self, value: int) -> None:
        self._increment.setValue(value)

    @property
    def _shape(self) -> QTreeWidgetItem:
        if self._shape_widget is None:
            self._shape_widget = QTreeWidgetItem(self._widget)
            self._shape_widget.setText(0, "")
        return self._shape_widget

    @_shape.setter
    def _shape(self, value: str) -> None:
        self._shape.setText(1, value)

    @property
    def indices(self) -> Indices:
        return Indices(self._start.value(), self._stop.value(), self._increment.value())

    def update_indices(self, number_of_images: int) -> None:
        """
        :param number_of_images: Number of images that will be loaded in from
                                 the current selection
        """
        # Cap the end value FIRST, otherwise setValue might fail if the
        # previous max val is smaller
        self._stop.setMaximum(number_of_images)
        self._stop.setValue(number_of_images)

        # Cap the start value to be end - 1 (ensure no negative value can be
        # set in case of loading failure)
        self._start.setMaximum(max(number_of_images - 1, 0))

        # Enforce the maximum step (ensure a minimum of 1)
        self._increment.setMaximum(max(number_of_images, 1))

    def set_preview(self, preview_mode: bool) -> None:
        if self._increment_spinbox is not None:
            if preview_mode:
                self._increment_spinbox.setValue(self._stop.maximum() // 10)
            else:
                self._increment_spinbox.setValue(1)

    def _update_expected_mem_usage(self, shape: tuple[int, int]) -> tuple[int, float]:
        num_images = size_calculator.number_of_images_from_indices(self._start.value(), self._stop.value(),
                                                                   self._increment.value())

        single_mem = size_calculator.full_size_MB(shape, dtype=np.float32)

        exp_mem = round(single_mem * num_images, 2)
        return num_images, exp_mem

    def update_shape(self, shape: int | tuple[int, int]) -> None:
        if isinstance(shape, int):
            self._shape = f"{str(shape)} images"
        else:
            num_images, exp_mem = self._update_expected_mem_usage(shape)
            self._shape = f"{num_images} images x {shape[0]} x {shape[1]}, {exp_mem}MB"
