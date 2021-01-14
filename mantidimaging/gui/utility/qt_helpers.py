# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
Module containing helper functions relating to PyQt.
"""

import os
from enum import IntEnum, auto
from logging import getLogger
from typing import Any, Tuple, Union, List

from PyQt5 import Qt
from PyQt5 import uic  # type: ignore
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QWidget, QSizePolicy, QAction, QMenu

from mantidimaging.core.utility import finder


class BlockQtSignals(object):
    """
    Used to block Qt signals from a selection of QWidgets within a context.
    """
    def __init__(self, q_objects: Union[QObject, List[QObject]]):
        if not isinstance(q_objects, list):
            q_objects = [q_objects]
        for obj in q_objects:
            assert isinstance(obj, Qt.QObject), \
                "This class must be used with QObjects"

        self.q_objects = q_objects
        self.previous_values = None

    def __enter__(self):
        self.previous_values = \
            [obj.blockSignals(True) for obj in self.q_objects]

    def __exit__(self, *args):
        for obj, prev in zip(self.q_objects, self.previous_values):
            obj.blockSignals(prev)


def compile_ui(ui_file, qt_obj=None):
    base_path = os.path.join(finder.get_external_location(__file__), finder.ROOT_PACKAGE)
    return uic.loadUi(os.path.join(base_path, ui_file), qt_obj)


def select_directory(field, caption):
    assert isinstance(field, Qt.QLineEdit), ("The passed object is of type {0}. This function only works with "
                                             "QLineEdit".format(type(field)))

    # open file dialogue and set the text if file is selected
    field.setText(Qt.QFileDialog.getExistingDirectory(caption=caption))


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


def add_property_to_form(label: str,
                         dtype: Union[Type, str],
                         default_value=None,
                         valid_values=None,
                         tooltip=None,
                         on_change=None,
                         form=None,
                         filters_view=None,
                         run_on_press=None) -> Tuple[Union[QLabel, QLineEdit], Any]:
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

    if dtype in ['str', Type.STR, 'tuple', Type.TUPLE, 'NoneType', Type.NONETYPE, 'list', Type.LIST]:
        # TODO for tuple with numbers add N combo boxes, N = number of tuple members
        right_widget = Qt.QLineEdit()
        right_widget.setToolTip(tooltip)
        right_widget.setText(default_value)

        if on_change is not None:
            right_widget.editingFinished.connect(lambda: on_change())

    elif dtype == 'int' or dtype == Type.INT:
        right_widget = Qt.QSpinBox()
        set_spin_box(right_widget, int)
        if on_change is not None:
            right_widget.editingFinished.connect(lambda: on_change())

    elif dtype == 'float' or dtype == Type.FLOAT:
        right_widget = Qt.QDoubleSpinBox()
        set_spin_box(right_widget, float)
        if on_change is not None:
            right_widget.editingFinished.connect(lambda: on_change())

    elif dtype == 'bool' or dtype == Type.BOOL:
        right_widget = Qt.QCheckBox()
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
        right_widget = Qt.QComboBox()
        right_widget.setSizeAdjustPolicy(Qt.QComboBox.AdjustToContents)
        if valid_values:
            right_widget.addItems(valid_values)
        if on_change is not None:
            right_widget.currentIndexChanged[int].connect(lambda: on_change())

    elif dtype == 'stack' or dtype == Type.STACK:
        from mantidimaging.gui.widgets.stack_selector import StackSelectorWidgetView
        right_widget = StackSelectorWidgetView(filters_view)
        if on_change is not None:
            right_widget.currentIndexChanged[int].connect(lambda: on_change())

    elif dtype == 'button' or dtype == Type.BUTTON:
        left_widget = Qt.QPushButton(label)
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
        left_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

    if right_widget:
        right_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
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
        if isinstance(item, Qt.QLayout):
            delete_all_widgets_from_layout(item)

        # Orphan child widgets (seting a None parent removes them from the
        # layout and marks them for deletion)
        elif item.widget() is not None:
            item.widget().setParent(None)


def populate_menu(menu: QMenu, actions_list: List[QAction]):
    for (menu_text, func) in actions_list:
        if func is None:
            menu.addSeparator()
        else:
            action = QAction(menu_text, menu)
            action.triggered.connect(func)
            menu.addAction(action)
