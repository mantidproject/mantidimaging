# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

# Mantid Repository : https://github.com/mantidproject/mantid
#
# Copyright &copy; 2017 ISIS Rutherford Appleton Laboratory UKRI,
#     NScD Oak Ridge National Laboratory, European Spallation Source
#     & Institut Laue - Langevin
# SPDX - License - Identifier: GPL - 3.0 +

# This file was taken from
# https://github.com/mantidproject/mantid/tree/aa5ed98034119ed3af79ea91527aa718c87c816c/qt/python/mantidqt/utils/qt/testing

import gc
import os
import pytest
import sys

import pyqtgraph
from PyQt5.QtWidgets import QApplication

_QAPP = QApplication.instance()

uncaught_exception = None
current_excepthook = sys.excepthook

pyqtgraph.setConfigOptions(imageAxisOrder="row-major")


def get_application(name=''):
    """
    Initialise and return the global application object
    :param name: Optional application name
    :return: Global application object
    """
    global _QAPP

    def handle_uncaught_exceptions(exc_type, exc_value, exc_traceback):
        """
        Qt slots swallows exceptions. We need to catch them, but not exit.
        """
        global uncaught_exception
        # store first exception caught
        if uncaught_exception is None:
            uncaught_exception = f"{exc_type=}, {exc_value=}"

        current_excepthook(exc_type, exc_value, exc_traceback)

    if _QAPP is None:
        _QAPP = QApplication([name])
        sys.excepthook = handle_uncaught_exceptions

    return _QAPP


def start_qapplication(cls):
    """
    Unittest decorator. Adds or augments the setUpClass classmethod
    to the given class. It starts the QApplication object
    if it is not already started
    @param cls: Class being decorated
    """
    def do_nothing(_):
        pass

    def setUp(self):
        global uncaught_exception
        uncaught_exception = None
        setUp_orig(self)

    def tearDown(self):
        tearDown_orig(self)
        if uncaught_exception is not None:
            pytest.fail(f"Uncaught exception {uncaught_exception}")

    def setUpClass(cls):
        cls.app = get_application()
        setUpClass_orig()

    def tearDownClass(cls):
        if os.getenv("APPLITOOLS_API_KEY") is None:
            gc.collect()
        tearDownClass_orig()

    setUp_orig = cls.setUp if hasattr(cls, 'setUp') else do_nothing
    tearDown_orig = cls.tearDown if hasattr(cls, 'tearDown') else do_nothing
    setUpClass_orig = cls.setUpClass if hasattr(cls, 'setUpClass') else do_nothing
    tearDownClass_orig = cls.tearDownClass if hasattr(cls, 'tearDownClass') else do_nothing
    setattr(cls, 'setUp', setUp)
    setattr(cls, 'tearDown', tearDown)
    setattr(cls, 'setUpClass', classmethod(setUpClass))
    setattr(cls, 'tearDownClass', classmethod(tearDownClass))
    return cls
