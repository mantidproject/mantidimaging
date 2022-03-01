# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import pytest


def _test_gui_system_filename_match(basename: str) -> bool:
    return "gui_system" in basename and "_test.py" in basename


def pytest_addoption(parser):
    parser.addoption("--run-system-tests", action="store_true", default=False, help="Run GUI system tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "system: GUI system tests")


def pytest_ignore_collect(path, config):
    # When running GUI system tests, ignore all other files
    if config.getoption("--run-system-tests") and path.isfile() and not _test_gui_system_filename_match(path.basename):
        return True
    else:
        return False


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-system-tests"):
        skip_system = pytest.mark.skip(reason="use --run-system-tests option to run")
        for item in items:
            if "system" in item.keywords:
                item.add_marker(skip_system)
