# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections import Counter

import pytest

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
    if config.getoption("--run-unit-tests"):
        allowed_markers.append(pytest.mark.unit.mark)
    if config.getoption("--run-eyes-tests"):
        allowed_markers.append(pytest.mark.eyes.mark)
    for item in items:
        if all(test not in item.nodeid for test in ["gui_system", "eyes_test"]):
            item.add_marker(pytest.mark.unit)
        if "gui_system" in item.nodeid:
            item.add_marker(pytest.mark.system)
        if "eyes_test" in item.nodeid:
            item.add_marker(pytest.mark.eyes)
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
