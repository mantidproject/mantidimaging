# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
import pytest

from mantidimaging.gui.widgets.stack_selector.view import _string_contains_all_parts, StackSelectorWidgetView
from mantidimaging.test_helpers import start_qapplication


@pytest.mark.parametrize("in_string,in_parts,expected", [
    ("flat_0001", ["Flat"], True),
    ("flat_0001", ["flat"], True),
    ("dark_0001", ["flat"], False),
    ("flat_0001", ["flat", "before"], False),
    ("flat_before_0001", ["flat", "before"], True),
])
def test_string_contains_all_parts(in_string, in_parts, expected):
    assert _string_contains_all_parts(in_string, in_parts) == expected


@start_qapplication
class StackSelectorWidgetViewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.view = StackSelectorWidgetView(None)

    def _add_items(self):
        self.view.addItems(["flat_0001", "dark_0001", "tomo_0001"])

    def test_try_to_select_relevant_stack(self):
        print(self.view)
        self._add_items()
        self.view.try_to_select_relevant_stack("dark")
        self.assertEqual(self.view.currentIndex(), 1)
        self.assertEqual(self.view.currentText(), "dark_0001")

        self.view.try_to_select_relevant_stack("flat")
        self.assertEqual(self.view.currentIndex(), 0)
        self.assertEqual(self.view.currentText(), "flat_0001")
