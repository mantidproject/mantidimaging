# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
Module containing helper functions relating to PyQt.
"""
from __future__ import annotations

import os
from enum import IntEnum, auto
from logging import getLogger
from typing import Any
from collections.abc import Callable

from PyQt5 import uic  # type: ignore
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QWidget, QSizePolicy, QAction,
                             QMenu, QPushButton, QLayout, QFileDialog, QComboBox)

from mantidimaging.core.utility import finder

MAX_SPIN_BOX = 2147483647
INPUT_DIALOG_FLAGS = Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint


class BlockQtSignals:
    """
    Used to block Qt signals from a selection of QWidgets within a context.
    """

    def __init__(self, q_objects: QObject | list[QObject]):
        if not isinstance(q_objects, list):
            q_objects = [q_objects]
        for obj in q_objects:
            assert isinstance(obj, QObject), \
                "This class must be used with QObjects"

        self.q_objects = q_objects
        self.previous_values = None

    def __enter__(self):
        self.previous_values = \
            [obj.blockSignals(True) for obj in self.q_objects]

    def __exit__(self, *args):
        for obj, prev in zip(self.q_objects, self.previous_values, strict=True):
            obj.blockSignals(prev)


def compile_ui(ui_file, qt_obj=None):
    base_path = finder.ROOT_PATH
    return uic.loadUi(os.path.join(base_path, ui_file), qt_obj)


def select_directory(field, caption):
    assert isinstance(field, QLineEdit), (f"The passed object is of type {type(field)}. This function only works with "
                                          "QLineEdit")

    # open file dialog and set the text if file is selected
    field.setText(QFileDialog.getExistingDirectory(caption=caption))


def get_value_from_qwidget(widget: QWidget):
    if isinstance(widget, QLineEdit):
        return widget.text()
    elif isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
        return widget.value()
    elif isinstance(widget, QCheckBox):
        return widget.isChecked()


class Type(IntEnum):
    STR = auto()
    TUPLE = auto()
    NONETYPE = auto()
    LIST = auto()
    FLOAT = auto()
    INT = auto()
    CHOICE = auto()
    BOOL = auto()
    LABEL = auto()
    STACK = auto()
    BUTTON = auto()


def on_change_and_disable(widget: QWidget, on_change: Callable):
    """
    Makes sure the widget is disabled while running the on_update method. This is required for spin boxes that
    continue increasing when generating a preview image is computationally intensive.
    :param widget: The widget to disable.
    :param on_change: The method to call when the widget has been changed.
    """
    widget.setEnabled(False)
    on_change()
    widget.setEnabled(True)


def add_property_to_form(label: str,
                         dtype: Type | str,
                         default_value=None,
                         valid_values=None,
                         tooltip=None,
                         on_change=None,
                         form=None,
                         filters_view=None,
                         run_on_press=None,
                         single_step_size=None) -> tuple[QLabel | QLineEdit, Any]:
    """
    Adds a property to the algorithm dialog.

    Handles adding basic data options to the UI.

    :param label: Label that describes the option
    :param dtype: Option data type (any of: file, int, float, bool, list)
    :param default_value: Optionally select the default value
    :param valid_values: Optionally provide the range or selection of valid
                         values
    :param tooltip: Optional tooltip text to show on property
    :param on_change: Function to be called when the property changes
    :param form: Form layout to optionally add the new widgets to
    :param filters_view: The Filter window view - passed to connect Type.STACK to the stack change events
    :param run_on_press: Run this function on press, specialisation for button.
    :param single_step_size: Optionally provide a step size for a SpinBox widget.
    """
    # By default assume the left hand side widget will be a label
    left_widget = QLabel(label)
    right_widget = None

    # sanitize default value
    if isinstance(default_value, str) and default_value.lower() == "none":
        default_value = None

    def set_spin_box(box, cast_func):
        """
        Helper function to set default options on a spin box.
        """
        if valid_values:
            box.setMinimum(valid_values[0])
            box.setMaximum(valid_values[1])
        else:
            box.setMinimum(0)
            box.setMaximum(10000)

        if default_value:
            box.setValue(cast_func(default_value))

        if single_step_size is not None:
            box.setSingleStep(single_step_size)
        elif cast_func == float:
            # Override the default step size for QDoubleSpinBox
            box.setSingleStep(0.1)

    if dtype in ['str', Type.STR, 'tuple', Type.TUPLE, 'NoneType', Type.NONETYPE, 'list', Type.LIST]:
        # TODO for tuple with numbers add N combo boxes, N = number of tuple members
        right_widget = QLineEdit()
        right_widget.setToolTip(tooltip)
        right_widget.setText(default_value)

        if on_change is not None:
            right_widget.editingFinished.connect(lambda: on_change())

    elif dtype == 'int' or dtype == Type.INT:
        right_widget = QSpinBox()
        right_widget.setKeyboardTracking(False)
        set_spin_box(right_widget, int)
        if on_change is not None:
            right_widget.valueChanged.connect(lambda: on_change_and_disable(right_widget, on_change))

    elif dtype == 'float' or dtype == Type.FLOAT:
        right_widget = QDoubleSpinBox()
        set_spin_box(right_widget, float)
        right_widget.setKeyboardTracking(False)
        if on_change is not None:
            right_widget.valueChanged.connect(lambda: on_change_and_disable(right_widget, on_change))

    elif dtype == 'bool' or dtype == Type.BOOL:
        right_widget = QCheckBox()
        if isinstance(default_value, bool):
            right_widget.setChecked(default_value)
        elif isinstance(default_value, str):
            right_widget.setChecked("True" == default_value)
        elif default_value is None:
            # have to pick something
            right_widget.setChecked(False)
        else:
            raise ValueError(f"Cannot convert value {default_value} to a Boolean.")

        if on_change is not None:
            right_widget.stateChanged[int].connect(lambda: on_change())

    elif dtype == "choice" or dtype == Type.CHOICE:
        right_widget = QComboBox()
        right_widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        if valid_values:
            right_widget.addItems(valid_values)
        if on_change is not None:
            right_widget.currentIndexChanged[int].connect(lambda: on_change())

    elif dtype == 'stack' or dtype == Type.STACK:
        from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView
        right_widget = DatasetSelectorWidgetView(filters_view, show_stacks=True)
        if on_change is not None:
            right_widget.currentIndexChanged[int].connect(lambda: on_change())

    elif dtype == 'button' or dtype == Type.BUTTON:
        left_widget = QPushButton(label)
        if run_on_press is not None:
            left_widget.clicked.connect(lambda: run_on_press())

    elif dtype == 'label' or dtype == Type.LABEL:
        # do nothing for label, just use the left widget
        pass

    else:
        raise ValueError("Unknown data type")

    if tooltip:
        if left_widget:
            left_widget.setToolTip(tooltip)

        if right_widget:
            right_widget.setToolTip(tooltip)

    # right widget check avoids printing debug msg for labels only
    if tooltip is None and right_widget is not None:
        log = getLogger(__name__)
        log.debug("Missing tooltip for %s", label)

    if left_widget:
        left_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    if right_widget:
        right_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    # Add to form layout
    if form is not None:
        form.addRow(left_widget, right_widget)

    return left_widget, right_widget


def delete_all_widgets_from_layout(lo):
    """
    Removes and deletes all child widgets form a layout.

    :param lo: Layout to clean
    """
    # For each item in the layout (removed as iterated)
    while lo.count() > 0:
        item = lo.takeAt(0)

        # Recurse for child layouts
        if isinstance(item, QLayout):
            delete_all_widgets_from_layout(item)

        # Orphan child widgets (seting a None parent removes them from the
        # layout and marks them for deletion)
        elif item.widget() is not None:
            item.widget().setParent(None)


def populate_menu(menu: QMenu, actions_list: list[QAction]):
    for (menu_text, func) in actions_list:
        if func is None:
            menu.addSeparator()
        else:
            action = QAction(menu_text, menu)
            action.triggered.connect(func)
            menu.addAction(action)
