# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock
from unittest.mock import DEFAULT, MagicMock, Mock, patch
from uuid import uuid4

import numpy as np

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.gui.windows.stack_choice.presenter import StackChoicePresenter
from mantidimaging.gui.windows.stack_choice.view import Notification
from mantidimaging.core.data.imagestack import ImageStack


class StackChoicePresenterTest(unittest.TestCase):

    @mock.patch("mantidimaging.gui.windows.stack_choice.presenter.StackChoiceView")
    def setUp(self, _):
        self.original_stack = th.generate_images()
        self.new_stack = th.generate_images()
        self.op_p = mock.MagicMock()
        self.uuid = uuid4()
        self.p = StackChoicePresenter(original_stack=self.original_stack,
                                      new_stack=self.new_stack,
                                      operations_presenter=self.op_p)
        self.v = self.p.view

    @mock.patch("mantidimaging.gui.windows.stack_choice.presenter.StackChoiceView")
    def test_presenter_doesnt_raise_lists_for_original_stack(self, _):
        single_stack_uuid = uuid4()
        original_stack = [(th.generate_images(), single_stack_uuid), (th.generate_images(), uuid4())]
        StackChoicePresenter(original_stack, mock.MagicMock(), mock.MagicMock())

    def test_show_calls_show_in_the_view(self):
        self.p.show()

        self.v.show.assert_called_once()

    def test_notify_choose_original(self):
        self.p.do_reapply_original_data = mock.MagicMock()

        self.p.notify(Notification.CHOOSE_ORIGINAL)

        self.p.do_reapply_original_data.assert_called_once()

    @patch.multiple("mantidimaging.gui.windows.stack_choice.presenter.StackChoicePresenter",
                    do_reapply_original_data=MagicMock(side_effect=RuntimeError),
                    show_error=DEFAULT)
    def test_notify_handles_exceptions(self, show_error: Mock):
        self.p.notify(Notification.CHOOSE_ORIGINAL)

        show_error.assert_called_once()

    def test_notify_choose_new_data(self):
        self.p.do_clean_up_original_data = mock.MagicMock()

        self.p.notify(Notification.CHOOSE_NEW_DATA)

        self.p.do_clean_up_original_data.assert_called_once()

    def test_do_reapply_original_data(self):
        self.p.close_view = mock.MagicMock()
        img1 = ImageStack(np.zeros((3, 3, 3)) + 1)
        img1.metadata = {"name": 1}
        img2 = ImageStack(np.zeros((3, 3, 3)) + 2)
        img2.metadata = {"name": 2}
        self.p.original_stack = img1
        self.p.new_stack = img2

        self.p.do_reapply_original_data()

        self.assertEqual(self.p.new_stack.data[0, 0, 0], 1)
        self.assertEqual(self.p.new_stack.metadata["name"], 1)
        self.assertTrue(self.v.choice_made)
        self.p.close_view.assert_called_once()

    def test_do_clean_up_original_data(self):
        self.p.original_stack = mock.MagicMock()
        self.p.close_view = mock.MagicMock()

        self.p.do_clean_up_original_data()

        self.assertTrue(self.v.choice_made)
        self.p.close_view.assert_called_once()

    def test_close_view_calls_close_on_view(self):
        self.p.close_view()

        self.v.close.assert_called_once()

    def test_close_view_sets_done_true(self):
        self.p.close_view()

        self.assertTrue(self.p.done)

    def test_do_toggle_lock_histograms(self):
        self.v.lockHistograms.isChecked.return_value = True
        self.p.notify(Notification.TOGGLE_LOCK_HISTOGRAMS)
        self.v.connect_histogram_changes.assert_called_once()

        self.v.lockHistograms.isChecked.return_value = False
        self.p.notify(Notification.TOGGLE_LOCK_HISTOGRAMS)
        self.v.disconnect_histogram_changes.assert_called_once()
