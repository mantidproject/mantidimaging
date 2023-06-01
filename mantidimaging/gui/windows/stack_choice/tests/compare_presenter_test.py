# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.gui.windows.stack_choice.compare_presenter import StackComparePresenter
from mantidimaging.gui.windows.stack_choice.view import Notification


class StackChoicePresenterTest(unittest.TestCase):

    def setUp(self):
        self.stack_one = th.generate_images()
        self.stack_two = th.generate_images()
        self.parent = mock.MagicMock()

    @mock.patch("mantidimaging.gui.windows.stack_choice.compare_presenter.StackChoiceView")
    def test_hides_buttons(self, view):
        self.presenter = StackComparePresenter(stack_one=self.stack_one, stack_two=self.stack_two, parent=self.parent)
        view.return_value.originalDataButton.hide.assert_called_once()
        view.return_value.newDataButton.hide.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.stack_choice.compare_presenter.StackChoiceView")
    def test_sets_choice_made(self, view):
        self.presenter = StackComparePresenter(stack_one=self.stack_one, stack_two=self.stack_two, parent=self.parent)
        self.assertIs(view.return_value.choice_made, True)

    @mock.patch("mantidimaging.gui.windows.stack_choice.compare_presenter.StackChoiceView")
    def test_show(self, view):
        self.presenter = StackComparePresenter(stack_one=self.stack_one, stack_two=self.stack_two, parent=self.parent)
        self.presenter.show()

        view.return_value.show.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.stack_choice.compare_presenter.StackChoiceView")
    def test_do_toggle_lock_histograms(self, view_class_mock):
        view_instance = view_class_mock.return_value

        view_instance.lockHistograms.isChecked.return_value = True
        self.presenter = StackComparePresenter(stack_one=self.stack_one, stack_two=self.stack_two, parent=self.parent)
        self.presenter.notify(Notification.TOGGLE_LOCK_HISTOGRAMS)
        view_instance.connect_histogram_changes.assert_called_once()

        view_instance.lockHistograms.isChecked.return_value = False
        self.presenter.notify(Notification.TOGGLE_LOCK_HISTOGRAMS)
        view_instance.disconnect_histogram_changes.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.stack_choice.compare_presenter.StackChoiceView")
    def test_titles_set(self, view: mock.Mock):
        self.presenter = StackComparePresenter(stack_one=self.stack_one, stack_two=self.stack_two, parent=self.parent)

        view.return_value.originalStackLabel.setText.assert_called_once_with(self.stack_one.name)
        view.return_value.newStackLabel.setText.assert_called_once_with(self.stack_two.name)
