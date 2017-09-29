from __future__ import (absolute_import, division, print_function)

import time
import threading

from logging import getLogger

from mantidimaging.core.utility.memory_usage import (
        get_memory_usage_linux_str)


class Progress(object):
    """
    Class used to perform basic progress monitoring and reporting.
    """

    @staticmethod
    def ensure_instance(p, *args, **kwargs):
        """
        Helper function used to select either a non-None Progress instance as a
        parameter, or simply create and configure a new one.
        """
        return p if p is not None else Progress(*args, **kwargs)

    def __init__(self, num_steps=1, task_name='Task'):
        self.task_name = task_name

        # Estimated number of steps (used to calculated percentage complete)
        self.end_step = 0
        self.set_estimated_steps(num_steps)

        # Current step being executed (0 denoting not started)
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
        self.update(0, 'init')

        # Log initial memory usage
        getLogger(__name__).debug(
                "Memory usage before execution: %s",
                get_memory_usage_linux_str())

    def __str__(self):
        return 'Progress(\n{})'.format('\n'.join(self.progress_history))

    def is_started(self):
        """
        Checks if the task has been started.

        A task starts when it reports it's first progress update.
        """
        return self.current_step > 0

    def is_completed(self):
        """
        Checks if the task has been marked as completed.
        """
        return self.complete

    def completion(self):
        """
        Gets the completion of the task in the range of 0.0 - 1.0
        """
        return round(self.current_step / self.end_step, 3)

    def execution_time(self):
        """
        Gets the total time this task has been executing.

        Total time is measured from the timestamp of the first progress message
        to the timestamp of the last progress message.
        """
        if len(self.progress_history) > 2:
            start = self.progress_history[1][0]
            last = self.progress_history[-1][0]
            return last - start
        else:
            return 0.0

    def set_estimated_steps(self, num_steps):
        """
        Sets the number of steps this task is expected to take to complete.
        """
        self.end_step = num_steps + 1

    def attach_callback(self, cb):
        self.progress_callbacks.append(cb)

    def update(self, steps=1, msg=''):
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

        # Log progress
        log = getLogger(__name__)
        log.debug("Progress: %f, Step: %s (%d/%d)",
                  self.completion(),
                  step_details[2],
                  step_details[1],
                  self.end_step)

        # Process progress callbacks
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
        log = getLogger(__name__)

        self.complete = True
        self.update(msg='complete')

        # Log elapsed time and final memory usage
        log.info("Elapsed time: %d sec.", self.execution_time())
        log.debug("Memory usage after execution: %s",
                  get_memory_usage_linux_str())
