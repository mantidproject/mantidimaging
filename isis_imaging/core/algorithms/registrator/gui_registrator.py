from __future__ import absolute_import, division, print_function

import warnings
import importlib

from PyQt5.Qt import QMenu, QAction
from isis_imaging.gui.main_window.mw_view import MainWindowView

def gui_register(qt_parent, package_dir):
    """
    :param qt_parent: Register the algorithms into this parent
    :param package_dir: The package from which to register all of the modules
    :param modules: The list of modules inside the package
    """

    assert isinstance(
        qt_parent,
        QMenu), "The object passed is not of a QMenu, and is not supported."

    main_window = qt_parent.parent().parent()
    assert isinstance(
        main_window,
        MainWindowView), "This must be the MainWindowView object!"

    # this should be menuFilters
    # add new section filters?

    group = QMenu(package_dir, qt_parent)
    qt_parent.addMenu(group)

    m = importlib.import_module(package_dir)

    # warn the user if one of the modules is missing the register method
    try:
        dialog = m._gui_register(main_window)
        action = QAction(package_dir, group)  # FIXME TODO this will be wrong!
        # the captured_dialog=dialog in the lambda captures THE ORIGINAL reference to the dialog
        # and when the user clicks the QAction in the QMenu the correct dialog is shown!
        # If we do not capture, EVERY QAction will .show() only the last dialogue! For proof of this
        # remove the capture, and set dialog=None after group.addAction,
        # Qt will raise NoneObject doesnt have .show()
        action.triggered.connect(
            lambda x, captured_dialog=dialog: captured_dialog.update_and_show())

        group.addAction(action)
    except AttributeError as err:
        warnings.warn(str(err))

    return qt_parent
