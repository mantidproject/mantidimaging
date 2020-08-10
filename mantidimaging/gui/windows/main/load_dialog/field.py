import os
from typing import Optional

from PyQt5.QtWidgets import QTreeWidgetItem, QWidget, QSpinBox, QTreeWidget, QHBoxLayout, QLabel


class Field:
    _widget: QTreeWidgetItem
    _spinbox_widget: Optional[QWidget] = None
    _start_spinbox: Optional[QSpinBox] = None
    _stop_spinbox: Optional[QSpinBox] = None
    _increment_spinbox: Optional[QSpinBox] = None

    def __init__(self, parent, tree: QTreeWidget, widget: QTreeWidgetItem):
        self._parent = parent
        self._tree = tree
        self._widget = widget
        self._path = None

    @property
    def widget(self) -> QTreeWidgetItem:
        """
        Returns the top-level widget of the section.
        All other fields are nested under it
        :return:
        """
        return self._widget

    @property
    def path(self):
        if self._path is None:
            self._path = QTreeWidgetItem(self._widget)
            self._path.setText(0, "Path")
        return self._path

    @path.setter
    def path(self, value: str):
        assert isinstance(value, str), "Can only display strings"
        if value != "":
            self.path.setText(1, value)
            self.widget.setText(1, self.file())

    def file(self) -> str:
        """
        :return: The file that the use has selected
        """
        return os.path.basename(self.path_text())

    def directory(self) -> str:
        """
        :return: The directory of the path as a Python string
        """
        return os.path.dirname(self.path_text())

    def path_text(self) -> str:
        """
        :return: The directory of the path as a Python string
        """
        return str(self.path.text(1))

    def _init_indices(self):
        indices_item = QTreeWidgetItem(self._widget)
        indices_item.setText(0, "File indices")
        _spinbox_layout = QHBoxLayout(self._tree.parent())

        self._start_spinbox = QSpinBox(self._tree.parent())
        _spinbox_layout.addWidget(QLabel("Start", self._tree.parent()))
        _spinbox_layout.addWidget(self._start_spinbox)

        self._stop_spinbox = QSpinBox(self._tree.parent())
        _spinbox_layout.addWidget(QLabel("Stop", self._tree.parent()))
        _spinbox_layout.addWidget(self._stop_spinbox)

        self._increment_spinbox = QSpinBox(self._tree.parent())
        _spinbox_layout.addWidget(QLabel("Increment", self._tree.parent()))
        _spinbox_layout.addWidget(self._increment_spinbox)

        self._spinbox_widget = QWidget(self._tree.parent())
        self._spinbox_widget.setLayout(_spinbox_layout)

        self._tree.setItemWidget(indices_item, 1, self._spinbox_widget)

    @property
    def start(self) -> QSpinBox:
        if self._spinbox_widget is None:
            self._init_indices()
        return self._start_spinbox

    @start.setter
    def start(self, value: int):
        self.start.setValue(value)

    @property
    def stop(self) -> QSpinBox:
        if self._spinbox_widget is None:
            self._init_indices()
        return self._stop_spinbox

    @stop.setter
    def stop(self, value: int):
        self.stop.setValue(value)

    @property
    def increment(self) -> QSpinBox:
        if self._spinbox_widget is None:
            self._init_indices()
        return self._increment_spinbox

    @increment.setter
    def increment(self, value: int):
        self.increment.setValue(value)
