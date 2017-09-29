from __future__ import absolute_import, division, print_function

import unittest

import mantidimaging.tests.test_helper as th

from mantidimaging.core.algorithms.progress_reporting import Progress


class ProgressTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ProgressTest, self).__init__(*args, **kwargs)

    def test_basic_single_setp(self):
        p = Progress()

        self.assertFalse(p.is_started())
        self.assertFalse(p.is_completed())
        self.assertEquals(len(p.progress_history), 1)
        self.assertEquals(p.completion(), 0.0)

        p.update_progress(msg='do a thing')

        self.assertTrue(p.is_started())
        self.assertEquals(len(p.progress_history), 2)
        self.assertEquals(p.completion(), 0.5)

        p.mark_complete()

        self.assertTrue(p.is_completed())
        self.assertEquals(len(p.progress_history), 3)
        self.assertEquals(p.completion(), 1.0)

    def test_multi_step(self):
        # Default to estimating a single step
        p = Progress()

        self.assertEquals(p.end_step, 2)
        self.assertEquals(len(p.progress_history), 1)
        self.assertEquals(p.completion(), 0.0)

        p.update_progress(msg='Estimate how complex I am')

        self.assertEquals(p.end_step, 2)
        self.assertEquals(len(p.progress_history), 2)
        self.assertEquals(p.completion(), 0.5)

        # First step to execute may decide that more steps are required
        p.set_estimated_steps(10)

        self.assertEquals(p.end_step, 11)
        self.assertEquals(len(p.progress_history), 2)
        self.assertEquals(p.completion(), 0.091)

        p.update_progress(steps=2, msg='Do two things')

        self.assertEquals(len(p.progress_history), 3)
        self.assertEquals(p.completion(), 0.273)

        p.update_progress(steps=2, msg='Do two more things')

        self.assertEquals(len(p.progress_history), 4)
        self.assertEquals(p.completion(), 0.455)

        p.update_progress(steps=3, msg='Do three things')

        self.assertEquals(len(p.progress_history), 5)
        self.assertEquals(p.completion(), 0.727)

        p.update_progress(steps=2, msg='Do two final things')

        self.assertEquals(len(p.progress_history), 6)
        self.assertEquals(p.completion(), 0.909)

        p.mark_complete()

        self.assertEquals(len(p.progress_history), 7)
        self.assertEquals(p.completion(), 1.0)

    def test_callbacks(self):
        mock = th.import_mock()

        cb1 = mock.MagicMock()
        cb2 = mock.MagicMock()
        callbacks = [cb1, cb2]

        def assert_call(expected_completion, expected_step, expected_msg):
            for m in callbacks:
                m.assert_called_once()

                _, kwargs = m.call_args
                self.assertEquals(kwargs['completion'], expected_completion)
                self.assertEquals(kwargs['step_details'][1], expected_step)
                self.assertEquals(kwargs['step_details'][2], expected_msg)

                m.reset_mock()

        p = Progress(5)
        p.attach_callback(cb1)
        p.attach_callback(cb2)

        p.update_progress(msg='First')
        assert_call(0.167, 1, 'First')

        p.update_progress(steps=2, msg='Second')
        assert_call(0.5, 3, 'Second')

        p.update_progress(msg='Third')
        assert_call(0.667, 4, 'Third')

        p.update_progress(msg='Last')
        assert_call(0.833, 5, 'Last')

        p.mark_complete()
        assert_call(1.0, 6, 'complete')


if __name__ == '__main__':
    unittest.main()
