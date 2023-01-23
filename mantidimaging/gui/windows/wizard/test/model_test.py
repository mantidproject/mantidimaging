# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

from mantidimaging.gui.windows.wizard.model import LoadedPredicate, HistoryPredicate, AndPredicate,\
    EnablePredicateFactory

HISTORY_EMPTY: dict = {}
HISTORY_1 = {'pixel_size': 0}
HISTORY_2 = {'operation_history': [{'name': 'FlatFieldFilter'}]}
HISTORY_3 = {'operation_history': [{'name': 'FlatFieldFilter'}, {'name': 'RoiNormalisationFilter'}]}


class WizardModelTest(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_loaded_predicate(self):
        pred = LoadedPredicate()
        self.assertFalse(pred(None))
        self.assertTrue(pred({}))

    def test_history_predicate_empty(self):
        self.assertRaises(ValueError, HistoryPredicate, "a")

    def test_history_predicate(self):
        pred_ff = HistoryPredicate("history:FlatFieldFilter")
        self.assertFalse(pred_ff(None))
        self.assertFalse(pred_ff(HISTORY_1))
        self.assertTrue(pred_ff(HISTORY_2))
        self.assertTrue(pred_ff(HISTORY_3))

    def test_and_predicate_empty(self):
        pred_empty = AndPredicate([])
        self.assertTrue(pred_empty(None))
        self.assertTrue(pred_empty(HISTORY_EMPTY))
        self.assertTrue(pred_empty(HISTORY_3))

    def test_and_predicate(self):
        h1 = HistoryPredicate("history:FlatFieldFilter")
        h2 = HistoryPredicate("history:RoiNormalisationFilter")
        pred_and = AndPredicate([h1, h2])
        self.assertFalse(pred_and(HISTORY_1))
        self.assertFalse(pred_and(HISTORY_2))
        self.assertTrue(pred_and(HISTORY_3))

    def test_enable_predicate_factory(self):
        pred_loaded = EnablePredicateFactory("loaded")
        self.assertFalse(pred_loaded(None))
        self.assertTrue(pred_loaded({}))

        pred_hist = EnablePredicateFactory("history:FlatFieldFilter, history:RoiNormalisationFilter")
        self.assertFalse(pred_hist(HISTORY_1))
        self.assertFalse(pred_hist(HISTORY_2))
        self.assertTrue(pred_hist(HISTORY_3))
