# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

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
from unittest import mock

import pyqtgraph
from mantidimaging.core.parallel.manager import create_and_start_pool, end_pool
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
        _QAPP.setStyle('Fusion')
        sys.excepthook = handle_uncaught_exceptions

    return _QAPP


def start_qapplication(cls):
    """
    Unittest decorator. Adds the functions for starting the QApplication object
    if it is not already started
    @param cls: Class being decorated
    """
    def setUp(self):
        global uncaught_exception
        uncaught_exception = None

    def tearDown(self):
        if uncaught_exception is not None:
            pytest.fail(f"Uncaught exception {uncaught_exception}")

    def setUpClass():
        cls.app = get_application()

    def tearDownClass():
        if os.getenv("APPLITOOLS_API_KEY") is None:
            gc.collect()

    return augment_test_setup_methods(cls, setUp, tearDown, setUpClass, tearDownClass)


def start_multiprocessing_pool(cls):
    def setUpClass():
        create_and_start_pool()

    def tearDownClass():
        end_pool()

    return augment_test_setup_methods(cls, setup_class=setUpClass, teardown_class=tearDownClass)


def mock_versions(cls):
    def setUpClass():
        cls.mock_get_version_patch = mock.patch(
            'mantidimaging.gui.windows.welcome_screen.presenter.versions.get_version')
        cls.mock_get_version = cls.mock_get_version_patch.start()
        cls.mock_get_version.return_value = "1.0.0"

        cls.mock_version_available_patch = mock.patch(
            'mantidimaging.gui.windows.welcome_screen.presenter.versions.get_conda_available_version')
        cls.mock_version_available = cls.mock_version_available_patch.start()
        cls.mock_version_available.return_value = "1.0.0"

    def tearDownClass():
        cls.mock_version_available_patch.stop()
        cls.mock_get_version_patch.stop()

    return augment_test_setup_methods(cls, setup_class=setUpClass, teardown_class=tearDownClass)


def augment_test_setup_methods(cls, setup=None, teardown=None, setup_class=None, teardown_class=None):
    """
    Adds or augments the setup and teardown methods for the given class.
    For sharing code between different unittest decorators.
    @param cls: class being decorated
    @param setup: the setUp function to be added
    @param teardown: the tearDown function to be added
    @param setup_class: the setUpClass function to be added
    @param teardown_class: the tearDownClass function to be added
    """
    def do_nothing(_):
        pass

    def setUp(self):
        setup(self)
        setup_orig(self)

    def tearDown(self):
        teardown_orig(self)
        teardown(self)

    def setUpClass(cls):
        setup_class()
        setup_class_orig()

    def tearDownClass(cls):
        teardown_class()
        teardown_class_orig()

    if setup:
        setup_orig = cls.setUp if hasattr(cls, 'setUp') else do_nothing
        cls.setUp = setUp

    if teardown:
        teardown_orig = cls.tearDown if hasattr(cls, 'tearDown') else do_nothing
        cls.tearDown = tearDown

    if setup_class:
        setup_class_orig = cls.setUpClass if hasattr(cls, 'setUpClass') else do_nothing
        cls.setUpClass = classmethod(setUpClass)

    if teardown_class:
        teardown_class_orig = cls.tearDownClass if hasattr(cls, 'tearDownClass') else do_nothing
        cls.tearDownClass = classmethod(tearDownClass)
    return cls
