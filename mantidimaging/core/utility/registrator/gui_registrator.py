from __future__ import absolute_import, division, print_function

from logging import getLogger

from PyQt5.Qt import QMenu, QAction

from mantidimaging.gui.algorithm_dialog import AlgorithmDialog
from mantidimaging.gui.main_window.mw_view import MainWindowView

from .registrator import do_importing

from .registrator import (
        get_child_modules,
        import_modules,
        register_modules_into
    )


def _gui_register_into_main_window(main_window, module):
    """
    This function is a callback from the registrator. It will handle the
    registration for the GUI.

    :param main_window: The main window object, at this point we are guaranteed
                        for it to be a MainWindowView because of the assertion
                        in gui_register

    :param module: The module that we are currently registering into the GUI.
    """
    log = getLogger(__name__)
    log.debug("Registering GUI: %s", module)

    menu = main_window.menuFilters

    # This will call the _gui_register function on each of the filters, where
    # _gui_register is found
    # We pass in the main_window reference to use it as the dialog's parent
    dialog = module._gui_register(main_window)

    # Make the UI fit the added components and prevent it from being resized
    # any smaller than this size
    dialog.adjustSize()
    dialog.setMinimumSize(dialog.size())

    # Refresh the stack list in the algorithm dialog whenever the active stacks
    # change
    main_window.active_stacks_changed.connect(dialog.refresh_stack_list)

    assert isinstance(dialog, AlgorithmDialog), (
            "Function _gui_register of {0} did not return the expected type. "
            "Check that the dialog is of type AlgorithmDialog and is "
            "returned at the end of the _gui_register "
            "function.".format(module))

    assert dialog.execute is not None, (
            "The execute function must be set manually! The module {0} has "
            "not set execute correctly".format(module))

    action = QAction(module.NAME, menu)

    # the captured_dialog=dialog in the lambda captures THE ORIGINAL reference
    # to the dialog and when the user clicks the QAction in the QMenu the
    # correct dialog is shown!
    # If we do not capture, EVERY QAction will .show() only the last dialogue,
    # because the reference is overwritten
    action.triggered.connect(
        lambda x, captured_dialog=dialog: captured_dialog.update_and_show())

    # finally add to the drop down menus
    menu.addAction(action)


def gui_register(qt_parent, package_name, ignored_packages):
    """
    Registers filter modules into the GUI.

    :param main_window: Instance of the main window

    :param package_name: Root package name of modules to register

    :param ignored_packages: Optional list of packages/modules to ignore
    """
    assert isinstance(qt_parent, QMenu), (
            "The object passed {0} is not a QMenu, and is not "
            "supported.".format(qt_parent))

    main_window = qt_parent.parent().parent()
    assert isinstance(main_window, MainWindowView), (
            "This must be the MainWindowView object! If it's not, it means "
            "the structure has been changed, and the registrator code needs "
            "to be adjusted")

    modules = get_child_modules(package_name, ignored_packages)
    modules = [m[1] for m in modules]

    loaded_modules = import_modules(
            modules, ['execute', 'NAME', '_gui_register'])

    register_modules_into(loaded_modules, main_window,
                          _gui_register_into_main_window)
