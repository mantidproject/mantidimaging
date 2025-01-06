# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import threading
import time
from logging import getLogger
from typing import NamedTuple, SupportsInt

from mantidimaging.core.utility.memory_usage import get_memory_usage_linux_str

ProgressHistory = NamedTuple('ProgressHistory', [('time', float), ('step', int), ('msg', str)])


class ProgressHandler:

    def __init__(self):
        self.progress = None

    def progress_update(self):
        raise NotImplementedError("Need to implement this method in the child class")


STEPS_TO_AVERAGE = 30


class Progress:
    """
    Class used to perform basic progress monitoring and reporting.
    """

    @staticmethod
    def ensure_instance(p: Progress | None = None, *args, num_steps: int | None = None, **kwargs) -> Progress:
        """
        Helper function used to select either a non-None Progress instance as a
        parameter, or simply create and configure a new one.
        """
        if p is None:
            p = Progress(*args, **kwargs)

        if num_steps:
            p.set_estimated_steps(num_steps)

        return p

    def __init__(self, num_steps: int = 1, task_name: str = 'Task') -> None:
        self.task_name = task_name

        # Current step being executed (0 denoting not started)
        self.current_step = 0
        # Estimated number of steps (used to calculated percentage complete)
        self.end_step = 0
        self.set_estimated_steps(num_steps)

        # Flag indicating completion
        self.complete = False

        # List of tuples defining progress history
        # (timestamp, step, message)
        self.progress_history: list[ProgressHistory] = []
        self.extra_info: dict | None = None

        # Lock used to synchronise modifications to the progress state
        self.lock = threading.Lock()

        # Handlers that receive notifications when progress updates occur
        self.progress_handlers: list[ProgressHandler] = []

        # Levels of nesting when used as a context manager
        self.context_nesting_level = 0

        # Flag to indicate cancellation of the current task
        self.cancel_msg = None

        # Add initial step to history
        self.update(0, 'init')

        # Log initial memory usage
        getLogger(__name__).debug("Memory usage before execution: %s", get_memory_usage_linux_str())

    def __str__(self):
        return 'Progress(\n{})'.format('\n'.join([str(ph) for ph in self.progress_history]))

    def __enter__(self):
        self.context_nesting_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context_nesting_level -= 1

        # Only when we have left the context at all levels is the task complete
        if self.context_nesting_level == 0:
            self.mark_complete()

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
        with self.lock:
            return round(self.current_step / self.end_step, 3)

    def last_status_message(self):
        """
        Gets the message from the last progress update.
        """
        with self.lock:
            if len(self.progress_history) > 0:
                msg = self.progress_history[-1][2]
                return msg if len(msg) > 0 else None

        return None

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

    def set_estimated_steps(self, num_steps: int):
        """
        Sets the number of steps this task is expected to take to complete.
        """
        self.current_step = 0
        self.end_step = num_steps

    def add_estimated_steps(self, num_steps):
        """
        Increments the number of steps this task is expected to take to
        complete.
        """
        self.end_step += num_steps

    def add_progress_handler(self, handler: ProgressHandler):
        """
        Adds a handler to receiver progress updates.
        :param handler: Instance of a progress handler
        """
        if not isinstance(handler, ProgressHandler):
            raise ValueError("Progress handlers must be of type ProgressHandler")

        self.progress_handlers.append(handler)
        handler.progress = self

    @staticmethod
    def _format_time(t: SupportsInt) -> str:
        t = int(t)
        return f'{t // 3600:02}:{t % 3600 // 60:02}:{t % 60:02}'

    def update(self,
               steps: int = 1,
               msg: str = "",
               force_continue: bool = False,
               extra_info: dict | None = None) -> None:
        """
        Updates the progress of the task.

        :param steps: Number of steps that have been completed since last call
                      to this function
        :param msg: Message describing current step
        :param force_continue: Prevent cancellation of the async progress
        """
        # Acquire lock while manipulating progress state
        with self.lock:
            # Update current step
            self.current_step += steps
            if self.current_step > self.end_step:
                self.end_step = self.current_step + 1

            mean_time = self.calculate_mean_time(self.progress_history)
            eta = mean_time * (self.end_step - self.current_step)

            msg = f"{msg} | {self.current_step}/{self.end_step} | " \
                  f"Time: {self._format_time(self.execution_time())}, ETA: {self._format_time(eta)}"
            step_details = ProgressHistory(time.perf_counter(), self.current_step, msg)
            self.progress_history.append(step_details)
            self.extra_info = extra_info

        # process progress callbacks
        for cb in self.progress_handlers:
            cb.progress_update()

        # Force cancellation on progress update
        if self.should_cancel and not force_continue:
            raise StopIteration('Task has been cancelled')

    @staticmethod
    def calculate_mean_time(progress_history: list[ProgressHistory]) -> float:
        if len(progress_history) > 1:
            average_over_steps = min(STEPS_TO_AVERAGE, len(progress_history))
            time_diff = progress_history[-1].time - progress_history[-average_over_steps].time

            return time_diff / (average_over_steps - 1)
        else:
            return 0

    def cancel(self, msg='cancelled'):
        """
        Mark the task tree that uses this progress instance for cancellation.

        Task should either periodically inspect should_cancel or have suitably
        many calls to update() to be cancellable.
        """
        self.cancel_msg = msg

    @property
    def should_cancel(self):
        """
        Checks if the task should be cancelled.
        """
        return self.cancel_msg is not None

    def mark_complete(self, msg='complete'):
        """
        Marks the task as completed.
        """
        log = getLogger(__name__)

        self.update(force_continue=True, msg=self.cancel_msg if self.should_cancel else msg)

        if not self.should_cancel:
            self.complete = True
            self.end_step = self.current_step

        # Log elapsed time and final memory usage
        log.info("Elapsed time: %d sec.", self.execution_time())
        log.debug("Memory usage after execution: %s", get_memory_usage_linux_str())
