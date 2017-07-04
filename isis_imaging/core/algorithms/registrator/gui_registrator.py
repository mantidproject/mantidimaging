from __future__ import absolute_import, division, print_function


from PyQt5.Qt import QMenu, QAction
from isis_imaging.gui.main_window.mw_view import MainWindowView
from .registrator import do_importing


def gui_register(qt_parent, package_dir):
    assert isinstance(
        qt_parent,
        QMenu), "The object passed is not of a QMenu, and is not supported."

    main_window = qt_parent.parent().parent()
    assert isinstance(
        main_window,
        MainWindowView), "This must be the MainWindowView object! If it's not, it means the structure has been " \
                         "changed, and the registrator code needs to be adjusted "

    do_importing(package_dir, '_gui_register', '_gui',
                 do_registering, main_window)

    return qt_parent


def do_registering(module, package_dir, main_window):
    menu = main_window.menuFilters
    dialog = module._gui_register(main_window)
    action = QAction(getattr(module, 'GUI_MENU_NAME', package_dir), menu)
    # the captured_dialog=dialog in the lambda captures THE ORIGINAL reference to the dialog
    # and when the user clicks the QAction in the QMenu the correct dialog is shown!
    # If we do not capture, EVERY QAction will .show() only the last dialogue! For proof of this
    # remove the capture, and set dialog=None after menu.addAction,
    # Qt will raise NoneObject doesnt have .show()
    action.triggered.connect(
        lambda x, captured_dialog=dialog: captured_dialog.update_and_show())
    menu.addAction(action)
