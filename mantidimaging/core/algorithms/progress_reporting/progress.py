from __future__ import (absolute_import, division, print_function)

import time
import threading


class Progress(object):

    def __init__(self, num_steps=1):
        # Estimated number of steps (used to calculated percentage complete)
        self.end_step = 0
        self.set_estimated_steps(num_steps)

        # Current step being executed
        # 0 is not started
        self.current_step = 0

        # Flag indicating completion
        self.complete = False

        # List of tuples defining progress history
        # (timestamp, step, message)
        self.progress_history = []

        # Lock used to synchronise modifications to the progress state
        self.lock = threading.Lock()

        # Functions that are called when the progress is updated
        self.progress_callbacks = []

        # Add initial step to history
        self.update_progress(0, 'init')

    def __str__(self):
        return 'Progress(\n{})'.format('\n'.join(self.progress_history))

    def is_started(self):
        return self.current_step > 0

    def is_completed(self):
        return self.complete

    def completion(self):
        return round(self.current_step / self.end_step, 3)

    def set_estimated_steps(self, num_steps):
        self.end_step = num_steps + 1

    def attach_callback(self, cb):
        self.progress_callbacks.append(cb)

    def update_progress(self, steps=1, msg=''):
        """
        Updates the progress of the task.

        :param steps: Number of steps that have been completed since last call
                      to this function
        :param msg: Message describing current step
        """
        # Acquire lock while manipulating progress state
        with self.lock:
            # Update current step
            self.current_step += steps
            if self.current_step > self.end_step:
                self.end_step = self.current_step + 1

            # Update progress history
            step_details = (time.clock(), self.current_step, msg)
            self.progress_history.append(step_details)

        if len(self. progress_callbacks) != 0:
            # Collect arguments for progress callback functions
            cb_args = {
                    'completion': self.completion(),
                    'step_details': step_details
                    }

            # Fire progress callbacks
            for cb in self.progress_callbacks:
                cb(**cb_args)

    def mark_complete(self):
        """
        Marks the task as completed.
        """
        self.complete = True
        self.update_progress(msg='complete')
