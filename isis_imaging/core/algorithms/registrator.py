from __future__ import (absolute_import, division, print_function)
import importlib
import os
import warnings
import sys
import argparse


def _cli(parser, package_dir, modules):
    assert isinstance(
        parser, argparse.ArgumentParser
    ), "The argument parser object was not of the correct type!"

    # this will make the group name equal the package
    # this means the core.filters will be separate from
    # core.filters.wip or any other additional folders
    group = parser.add_argument_group(package_dir)

    # we specify the full absolute path and append the package name
    # the code underneath does import core.filters.package_name
    for module in modules:
        full_module = package_dir + '.' + module
        m = importlib.import_module(full_module)

        # warn the user if one of the modules is missing the cli_register method
        try:
            m.cli_register(group)
        except AttributeError:
            cli_register_warning = "The module " + full_module + " does NOT have a cli_register(parser) method!"
            warnings.warn(cli_register_warning)
    return parser


def _gui(qt_parent, package_dir, modules):
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

    # we specify the full absolute path and append the package name
    # the code underneath does import core.filters.package_name
    for module in modules:
        # register _into_ the dialogue
        full_module = package_dir + '.' + module
        m = importlib.import_module(full_module)

        # warn the user if one of the modules is missing the register method
        try:
            dialog = m.gui_register(main_window)
            action = QAction(module, group)
            # the captured_dialog=dialog in the lambda captures THE ORIGINAL reference to the dialog
            # and when the user clicks the QAction in the QMenu the correct dialog is shown!
            # If we do not capture, EVERY QAction will .show() only the last dialogue! For proof of this
            # remove the capture, and set dialog=None after group.addAction,
            # Qt will raise NoneObject doesnt have .show()
            action.triggered.connect(
                lambda x, captured_dialog=dialog: captured_dialog.update_and_show()
            )
            group.addAction(action)
        except AttributeError as err:
            warnings.warn(str(err))

    return qt_parent


def register_into(obj,
                  directory=None,
                  package="core/filters",
                  func=_cli,
                  norecurse=False):
    """
    This function will build the path to the specified package, and then import all of the modules from it,
    and call cli_register if _cli is specified, or gui_register if _gui is specified.

    :param obj: the obj into which the modules will be registered,
                this is simply forwarded onto the actual functions that do the dynamic registering
    :param directory: The directory to be walked for python modules.
                      This parameter is currently being added to ease unit testing.
    :param package: The internal package from which modules will be imported
    :param func: Two built in functions are provided, registrator._cli and registrator._gui, for registration into the
                 command line interface (CLI) or the graphical user interface (GUI). A custom function can be passed
                 if the behaviour needs to be extended or overriden
    """
    # sys path 0 will give us the parent directory of the package, and we append the internal package location
    if not directory:
        directory = os.path.join(sys.path[0], package)

    all_files = os.walk(directory)

    # replace the / with . to match python package syntax
    for root, dirs, files in all_files:
        # Find the package string within the _full_ path, crop everything in front of it and replace the / with .
        # We replace / with . so that the import statement below can work
        # For example: /home/user/Documents/isis_imaging/isis_imaging/core/filters
        # becomes <trim /home/user/Documents/isis_imaging/isis_imaging/ >, replace / to . in rest -> core/filters
        package_dir = root[root.find(package):].replace('/', '.')

        # specify the checks to remove specific files
        checks = [
            lambda x: '.py' in x,  # removes all files that DON'T have .py in the name
            lambda x: '.pyc' not in x,  # removes all files that DO have .pyc in the name
            lambda x: '__init__' not in x,  # removes all files that DO have __init__ in the name
            lambda x: 'registrator.py' not in x  # removes all files that have this module's name in the name
        ]

        # apply all of the above checks
        for check in checks:
            files = filter(check, files)

        # trim the .py in the name to get only the filename
        modules = map(lambda f: f[:-3], files)
        obj = func(obj, package_dir, modules)
        if norecurse:
            return obj

    return obj


def all_modules(package):
    # type: (str) -> [str]
    everything = []

    def append_to_foreign_object(obj, package_dir, modules):
        # simply ignore other params and append the modules
        everything.append(modules)

    register_into([], None, package, append_to_foreign_object, norecurse=True)
    return [item for sublist in everything for item in sublist]
