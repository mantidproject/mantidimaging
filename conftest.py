# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections import Counter

import pytest
from PyQt5 import QtCore
from PyQt5.QtGui import QFont

from mantidimaging.core.utility.leak_tracker import leak_tracker


def pytest_addoption(parser):
    parser.addoption("--run-system-tests", action="store_true", default=False, help="Run GUI system tests")
    parser.addoption("--run-unit-tests", action="store_true", default=False, help="Run unit tests")
    parser.addoption("--run-eyes-tests", action="store_true", default=False, help="Run eyes tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "system: GUI system tests")
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "eyes: eyes tests")


allowed_markers = []
skipped_tests = []


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-system-tests"):
        allowed_markers.append(pytest.mark.system.mark)
    if config.getoption("--run-eyes-tests"):
        allowed_markers.append(pytest.mark.eyes.mark)
    if config.getoption("--run-unit-tests") or len(allowed_markers) == 0:
        allowed_markers.append(pytest.mark.unit.mark)
    for item in items:
        if "gui_system" in item.nodeid:
            item.add_marker(pytest.mark.system)
        elif "eyes_test" in item.nodeid:
            item.add_marker(pytest.mark.eyes)
        else:
            item.add_marker(pytest.mark.unit)
        if any(mark in allowed_markers for mark in item.own_markers):
            pass
        else:
            item.add_marker(pytest.mark.skip(reason="Test not selected"))
            skipped_tests.append(item.nodeid)


# Leak track for tests
# To use, set autouse to True
# Add:
#  leak_tracker.add(self, msg=name)
# to the constructor of class of interest.
@pytest.fixture(autouse=False)
def leak_test_stats():
    yield
    live_objects = leak_tracker.live_objects()
    c = Counter(type(item.ref()) for item in live_objects)
    if c.total():
        print("Leaked item stats:")
        for item_type, count in c.items():
            print(f"{item_type}: {count}")

    # leak_tracker.clear() # Uncomment to clear after each test
    # print(leak_tracker.pretty_print(debug_owners=True)) # uncomment to track leaks


@pytest.fixture(autouse=True)
def setup_QSettings():
    settings = QtCore.QSettings('mantidproject', 'Mantid Imaging')
    default_font = QFont()
    extra_style_default = {

        # Density Scale
        'density_scale': '-5',

        # font
        'font_size': str(default_font.pointSize()) + 'px',
    }
    settings.setValue('extra_style_default', extra_style_default)
    if settings.value('extra_style') is None:
        settings.setValue('extra_style', extra_style_default)
