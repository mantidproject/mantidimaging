# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

from unittest import mock

from mantidimaging.core.utility.progress_reporting import Progress, ProgressHandler
from mantidimaging.core.utility.progress_reporting.progress import ProgressHistory


class ProgressTest(unittest.TestCase):

    def test_basic_single_step(self):
        p = Progress(num_steps=2)

        self.assertFalse(p.is_started())
        self.assertFalse(p.is_completed())
        self.assertEqual(len(p.progress_history), 1)
        self.assertEqual(p.completion(), 0.0)

        p.update(msg="do a thing")

        self.assertTrue(p.is_started())
        self.assertEqual(len(p.progress_history), 2)
        self.assertEqual(p.completion(), 0.5)

        p.mark_complete()

        self.assertTrue(p.is_completed())
        self.assertEqual(len(p.progress_history), 3)
        self.assertEqual(p.completion(), 1.0)

    def test_set_steps_resets_current_step(self):
        p = Progress(num_steps=2)
        p.update(steps=1)
        self.assertEqual(p.current_step, 1)
        p.set_estimated_steps(10)
        self.assertEqual(p.current_step, 0)
        self.assertEqual(p.end_step, 10)

    def test_multi_step(self):
        # Default to estimating a single step
        p = Progress(num_steps=2)

        self.assertEqual(p.end_step, 2)
        self.assertEqual(len(p.progress_history), 1)
        self.assertEqual(p.completion(), 0.0)

        p.update(msg="Estimate how complex I am")

        self.assertEqual(p.end_step, 2)
        self.assertEqual(len(p.progress_history), 2)
        self.assertEqual(p.completion(), 0.5)

        # First step to execute may decide that more steps are required
        p.add_estimated_steps(10)

        self.assertEqual(p.end_step, 12)
        self.assertEqual(len(p.progress_history), 2)
        self.assertEqual(p.completion(), 0.083)

        p.update(steps=2, msg="Do two things")

        self.assertEqual(len(p.progress_history), 3)
        self.assertEqual(p.completion(), 0.25)

        p.update(steps=2, msg="Do two more things")

        self.assertEqual(len(p.progress_history), 4)
        self.assertEqual(p.completion(), 0.417)

        p.update(steps=3, msg="Do three things")

        self.assertEqual(len(p.progress_history), 5)
        self.assertEqual(p.completion(), 0.667)

        p.mark_complete()

        self.assertEqual(len(p.progress_history), 6)
        self.assertEqual(p.completion(), 1.0)

    def test_multi_step_early_completion(self):
        # Default to estimating a single step
        p = Progress(num_steps=2)

        self.assertEqual(p.end_step, 2)
        self.assertEqual(len(p.progress_history), 1)
        self.assertEqual(p.completion(), 0.0)

        p.update(msg="Estimate how complex I am")

        self.assertEqual(p.end_step, 2)
        self.assertEqual(len(p.progress_history), 2)
        self.assertEqual(p.completion(), 0.5)

        # First step to execute may decide that more steps are required
        p.add_estimated_steps(10)

        self.assertEqual(p.end_step, 12)
        self.assertEqual(len(p.progress_history), 2)
        self.assertEqual(p.completion(), 0.083)

        p.update(steps=2, msg="Do two things")

        self.assertEqual(len(p.progress_history), 3)
        self.assertEqual(p.completion(), 0.25)

        # Finish early
        p.mark_complete()

        self.assertEqual(len(p.progress_history), 4)
        self.assertEqual(p.completion(), 1.0)

    def test_multi_step_step_increments(self):
        # Default to estimating a single step
        p = Progress(num_steps=2)

        self.assertEqual(p.end_step, 2)
        self.assertEqual(len(p.progress_history), 1)
        self.assertEqual(p.completion(), 0.0)

        p.update(msg="Estimate how complex I am")

        self.assertEqual(p.end_step, 2)
        self.assertEqual(len(p.progress_history), 2)
        self.assertEqual(p.completion(), 0.5)

        # First step to execute may decide that more steps are required
        p.add_estimated_steps(8)

        self.assertEqual(p.end_step, 10)
        self.assertEqual(len(p.progress_history), 2)
        self.assertEqual(p.completion(), 0.1)

        p.update(steps=2, msg="Do two things")

        self.assertEqual(len(p.progress_history), 3)
        self.assertEqual(p.completion(), 0.3)

        # Finish early
        p.mark_complete()

        self.assertEqual(len(p.progress_history), 4)
        self.assertEqual(p.completion(), 1.0)

    def test_callbacks(self):
        cb1 = mock.create_autospec(ProgressHandler, instance=True)
        cb2 = mock.create_autospec(ProgressHandler, instance=True)
        callbacks = [cb1, cb2]

        def assert_call(expected_completion, expected_step, expected_msg):
            for m in callbacks:
                m.progress_update.assert_called_once()
                m.reset_mock()

        p = Progress(5)
        p.add_progress_handler(cb1)
        p.add_progress_handler(cb2)

        p.update(msg="First")
        assert_call(0.167, 1, "First")

        p.update(steps=2, msg="Second")
        assert_call(0.5, 3, "Second")

        p.update(msg="Third")
        assert_call(0.667, 4, "Third")

        p.update(msg="Last")
        assert_call(0.833, 5, "Last")

        p.mark_complete()
        assert_call(1.0, 6, "complete")

    def test_add_callback_incorrect_type(self):
        p = Progress(5)

        not_a_progress_handler = "I'm a string!"

        with self.assertRaises(ValueError):
            p.add_progress_handler(not_a_progress_handler)

    def test_context(self):
        p = Progress(num_steps=2)

        self.assertFalse(p.is_started())
        self.assertFalse(p.is_completed())
        self.assertEqual(len(p.progress_history), 1)
        self.assertEqual(p.completion(), 0.0)

        with p:
            p.update(msg="do a thing")

            self.assertTrue(p.is_started())
            self.assertEqual(len(p.progress_history), 2)
            self.assertEqual(p.completion(), 0.5)

        self.assertTrue(p.is_completed())
        self.assertEqual(len(p.progress_history), 3)
        self.assertEqual(p.completion(), 1.0)

    def test_context_nested(self):
        p = Progress(num_steps=2)

        self.assertFalse(p.is_started())
        self.assertFalse(p.is_completed())
        self.assertEqual(len(p.progress_history), 1)
        self.assertEqual(p.completion(), 0.0)

        with p:
            p.update(msg="do a thing")
            self.assertEqual(len(p.progress_history), 2)

            for i in range(5):
                with p:
                    p.update(msg="do a thing in a loop nested in the other thing")

                self.assertEqual(len(p.progress_history), 3 + i)
                self.assertFalse(p.is_completed())

            self.assertEqual(len(p.progress_history), 7)
            self.assertFalse(p.is_completed())

        self.assertTrue(p.is_completed())
        self.assertEqual(len(p.progress_history), 8)
        self.assertEqual(p.completion(), 1.0)

    def test_cancellation(self):
        p = Progress()
        p.add_estimated_steps(10)

        with p:
            for i in range(10):
                if i < 6:
                    p.update()

                    if i == 5:
                        p.cancel("nope")
                        self.assertTrue(p.should_cancel)

                else:
                    with self.assertRaises(StopIteration):
                        p.update()

        self.assertFalse(p.is_completed())
        self.assertTrue(p.should_cancel)

    def test_format_time(self):
        self.assertEqual(Progress._format_time(0), "00:00:00")
        self.assertEqual(Progress._format_time(1), "00:00:01")
        self.assertEqual(Progress._format_time(61), "00:01:01")
        self.assertEqual(Progress._format_time(3599), "00:59:59")
        self.assertEqual(Progress._format_time(3666), "01:01:06")

    def test_calculate_mean_time(self):
        progress_history = []

        progress_history.append(ProgressHistory(100, 0, "", None))
        self.assertEqual(Progress.calculate_mean_time(progress_history), 0)

        # first step 5 seconds
        progress_history.append(ProgressHistory(105, 1, "", None))
        self.assertEqual(Progress.calculate_mean_time(progress_history), 5)

        # second step 10 seconds
        progress_history.append(ProgressHistory(115, 2, "", None))
        self.assertEqual(Progress.calculate_mean_time(progress_history), 7.5)

        for i in range(1, 50):
            # add many 2 second steps
            progress_history.append(ProgressHistory(115 + (i * 2), 2 + (i * 2), "", None))
        self.assertEqual(Progress.calculate_mean_time(progress_history), 2)


if __name__ == "__main__":
    unittest.main()
