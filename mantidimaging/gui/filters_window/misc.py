from __future__ import absolute_import, division, print_function

from PyQt5 import Qt

from mantidimaging.gui.main_window.load_dialog import select_file


def add_property_to_form(label,
                         dtype,
                         default_value=None,
                         valid_values=None,
                         tooltip=None,
                         form=None):
    """
    Adds a property to the algorithm dialog.

    Handles adding basic data options to the UI.

    :param label: Label that describes the option
    :param dtype: Option data type (any of: file, int, float, bool, list)
    :param default_value: Optionally select the default value
    :param valid_values: Optionally provide the range or selection of valid
                         values
    :param form: Form layout to optionally add the new widgets to
    """
    # By default assume the left hand side widget will be a label
    left_widget = Qt.QLabel(label)
    right_widget = None

    def set_spin_box(box):
        """
        Helper function to set default options on a spin box.
        """
        if valid_values:
            box.setMinimum(valid_values[0])
            box.setMaximum(valid_values[1])
        if default_value:
            box.setValue(default_value)

    def assign_tooltip(widgets):
        """
        Helper function to assign tooltips to widgets.
        """
        if tooltip:
            for w in widgets:
                w.setToolTip(tooltip)

    # Set up data type dependant widgets
    if dtype == 'file':
        left_widget = Qt.QLineEdit()
        right_widget = Qt.QPushButton(label)
        assign_tooltip([left_widget, right_widget])
        right_widget.clicked.connect(
                lambda: select_file(left_widget, label))
    elif dtype == 'int':
        right_widget = Qt.QSpinBox()
        assign_tooltip([right_widget])
        set_spin_box(right_widget)
    elif dtype == 'float':
        right_widget = Qt.QDoubleSpinBox()
        assign_tooltip([right_widget])
        set_spin_box(right_widget)
    elif dtype == 'bool':
        left_widget = None
        right_widget = Qt.QCheckBox(label)
        assign_tooltip([right_widget])
        if isinstance(default_value, bool):
            right_widget.setChecked(default_value)
    elif dtype == 'list':
        right_widget = Qt.QComboBox()
        assign_tooltip([right_widget])
        if valid_values:
            right_widget.addItems(valid_values)
    elif dtype == 'label':
        pass
    else:
        raise ValueError("Unknown data type")

    # Add to form layout
    if form is not None:
        form.addRow(left_widget, right_widget)

    return (left_widget, right_widget)
