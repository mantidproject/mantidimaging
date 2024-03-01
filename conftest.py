# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from collections import Counter

import pytest

from mantidimaging.core.utility.leak_tracker import leak_tracker


def _test_gui_system_filename_match(basename: str) -> bool:
    return "gui_system" in basename and "_test.py" in basename


def _test_normal_filename_match(path) -> bool:
    return "gui_system" not in path.basename and "eyes_tests" not in str(path) and "_test.py" in path.basename


def pytest_addoption(parser):
    parser.addoption("--run-system-tests", action="store_true", default=False, help="Run GUI system tests")
    parser.addoption("--run-tests", action="store_true", default=False, help="Run normal tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "system: GUI system tests")
    config.addinivalue_line("markers", "normal: normal tests")


def pytest_ignore_collect(path, config):
    # When running GUI system tests, ignore all other files
    if config.getoption("--run-system-tests") and path.isfile() and not _test_gui_system_filename_match(path.basename):
        return True
    elif config.getoption("--run-tests") and path.isfile() and not _test_normal_filename_match(path):
        return True
    else:
        return False


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-system-tests"):
        skip_system = pytest.mark.skip(reason="use --run-system-tests option to run")
        for item in items:
            if "system" in item.keywords:
                item.add_marker(skip_system)
    elif not config.getoption("--run-tests"):
        skip_system = pytest.mark.skip(reason="use --run-tests option to run")
        for item in items:
            if "system" not in item.keywords and "eyes_tests" not in item.path:
                item.add_marker(skip_system)


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
