# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

# Mantid Repository : https://github.com/mantidproject/mantid
#
# Copyright &copy; 2017 ISIS Rutherford Appleton Laboratory UKRI,
#     NScD Oak Ridge National Laboratory, European Spallation Source
#     & Institut Laue - Langevin
# SPDX - License - Identifier: GPL - 3.0 +

# This file was taken from
# https://github.com/mantidproject/mantid/tree/aa5ed98034119ed3af79ea91527aa718c87c816c/qt/python/mantidqt/utils/qt/testing
from __future__ import absolute_import

import gc
import sys
import traceback

from PyQt5.QtWidgets import QApplication

_QAPP = QApplication.instance()


def get_application(name=''):
    """
    Initialise and return the global application object
    :param name: Optional application name
    :return: Global appliction object
    """
    global _QAPP

    def exception_handler(exctype, value, tb):
        traceback.print_exception(exctype, value, tb)
        sys.exit(1)

    if _QAPP is None:
        _QAPP = QApplication([name])
        sys.excepthook = exception_handler

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

    def setUpClass(cls):
        get_application()
        setUpClass_orig()

    def tearDownClass(cls):
        gc.collect()

    setUpClass_orig = cls.setUpClass if hasattr(cls, 'setUpClass') else do_nothing
    setattr(cls, 'setUpClass', classmethod(setUpClass))
    setattr(cls, 'tearDownClass', classmethod(tearDownClass))
    return cls
