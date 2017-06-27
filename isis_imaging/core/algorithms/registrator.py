from __future__ import (absolute_import, division, print_function)
import importlib
import os
import warnings
import sys
import argparse


def _cli(parser, package_dir):
    assert isinstance(
        parser, argparse.ArgumentParser
    ), "The argument parser object was not of the correct type!"

    # we specify the full absolute path and append the package name
    # the code underneath does import core.filters.package_name
    m = importlib.import_module(package_dir)

    # warn the user if one of the modules is missing the _cli_register method
    if getattr(m, '_cli_register', None):
        # this will make the group name equal the package
        # this means the core.filters will be separate from
        # core.filters.wip or any other additional folders
        group = parser.add_argument_group(package_dir)
        m._cli_register(group)
    else:
        _cli_register_warning = "The package " + package_dir + \
            " does NOT have a _cli_register(parser) method!"
        warnings.warn(_cli_register_warning)
    return parser


def _gui(qt_parent, package_dir):
    """
    :param qt_parent: Register the algorithms into this parent
    :param package_dir: The package from which to register all of the modules
    :param modules: The list of modules inside the package
    """
    from PyQt4.QtGui import QMenu, QAction
    from gui.main_window.mw_view import ImgpyMainWindowView
    assert isinstance(
        qt_parent,
        QMenu), "The object passed is not of a QMenu, and is not supported."

    main_window = qt_parent.parent().parent()
    assert isinstance(
        main_window,
        ImgpyMainWindowView), "This must be the ImgpyMainWindowView object!"
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


def register_into(obj,
                  directory=None,
                  package="core/filters",
                  func=_cli,
                  ignore_packages=None):
    """
    This function will build the path to the specified package, and then import all of the modules from it,
    and call _cli_register if _cli is specified, or _gui_register if _gui is specified.

    :param ignore_packages:
    :param obj: the obj into which the modules will be registered,
                this is simply forwarded onto the actual functions that do the dynamic registering
    :param directory: The directory to be walked for python modules. If not provided sys.path[0] will be used.
    :param package: The internal package from which modules will be imported
    :param func: Two built in functions are provided, registrator._cli and registrator._gui, for registration into the
                 command line interface (CLI) or the graphical user interface (GUI). A custom function can be passed
                 if the behaviour needs to be extended or overridden
    """
    if ignore_packages is None:
        ignore_packages = ["core/filters", "core/filters/wip"]

    # sys path 0 will give us the parent directory of the package, and we
    # append the internal package location
    if not directory:
        directory = os.path.join(sys.path[0], package)

    all_files = os.walk(directory)

    # replace the / with . to match python package syntax
    for root, dirs, files in all_files:
        package_dir = root[root.find(package):].replace('/', '.')
        if package_dir in ignore_packages:
            continue
        obj = func(obj, package_dir)

    return obj
