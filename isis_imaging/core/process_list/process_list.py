from __future__ import absolute_import, division, print_function

import cStringIO
import inspect
import os
# using pickle instead of dill, because dill is not available on SCARF
import pickle
from ast import literal_eval
from collections import deque

from isis_imaging.core.algorithms import finder

DEFAULT_ARGUMENT_SEPARATOR = ' '
DEFAULT_FUNCTION_SEPARATOR = ';'
DEFAULT_TUPLE_SEPARATOR = ')'


def _entry_from_string(entry, arg_separator=DEFAULT_ARGUMENT_SEPARATOR, tuple_separator=DEFAULT_TUPLE_SEPARATOR):
    whitespace = entry.find(arg_separator)
    package = entry[:whitespace]
    entry = entry[whitespace + 1:]

    whitespace = entry.find(arg_separator)
    func = entry[:whitespace]
    entry = entry[whitespace + 1:]

    tuple_end_brace = entry.find(tuple_separator) + 1
    # literal eval to convert into the actual tuple type
    args = literal_eval(entry[:tuple_end_brace])
    entry = entry[tuple_end_brace + 1:]

    kwargs = literal_eval(entry)
    return package, func, args, kwargs


def load(file=None):
    return pickle.load(open(file, "rb"))


def from_string(string, cls=None, arg_separator=DEFAULT_ARGUMENT_SEPARATOR, func_separator=DEFAULT_FUNCTION_SEPARATOR):
    if cls is not None:
        assert isinstance(
            cls, ProcessList), "The class parameter is not of the correct type ProcessList!"
    else:
        cls = ProcessList()

    # split on func separator and remove any 0 length strings
    separated_string = filter(lambda s: len(
        s) > 0, string.split(DEFAULT_FUNCTION_SEPARATOR))
    try:
        for entry in separated_string:
            cls._store_string(*_entry_from_string(
                entry, arg_separator, DEFAULT_TUPLE_SEPARATOR))
    except (AttributeError, SyntaxError, ValueError) as e:
        raise ValueError(
            "Error encountered while processing from the input string. The formatting may be invalid." + str(e))

    return cls


class ProcessList(object):
    """
    Stores a queue of functions to be executed in first-in first-out order.
    Currently only works with ISIS_IMAGING internal functions.

    When it needs to be more generic changes to finder.get_package need to be made
    to account that the function package can be in any arbitrary folder. This is
    currently possible via the finder.get_package's root_package argument, but maybe
    it could be automated further.
    """

    def __init__(self):
        self._dequeue = deque()

    def __str__(self):
        # call with default separators
        return self.to_string(DEFAULT_ARGUMENT_SEPARATOR, '\n')

    def __len__(self):
        return len(self._dequeue)

    def __eq__(self, rhs):
        return self._dequeue == rhs._dequeue

    def clear(self):
        self._dequeue.clear()

    def store(self, func, *args, **kwargs):
        """
        Store a function in the process list to be executed later. The arguments must be literal values.
        Note: More arguments can be appended when the funciton is called for execution.

        :param func: This works with a function reference, because metadata needs to be read from the funciton.
        :param args: Arguments that will be forwarded to the function. They must be literal values.
        :param kwargs: Keyword arguments that will be forwarded to the function. They must be literal values.
        """
        if(isinstance(func, str)):
            self._store_string(func, args, kwargs)
        else:
            self._store_func(func, args, kwargs)

    def _store_func(self, func, args, kwargs):
        assert set(kwargs.viewkeys()).issubset(inspect.getargspec(func)[0]), \
            "One or more of the keyword arguments provided were NOT found in the function's declaration!"

        func_package = finder.get_package(func.func_globals['__file__'])
        func_name = func.func_name
        self._store_string(func_package, func_name, args, kwargs)

    def _store_string(self, package, func, args, kwargs):
        self._dequeue.append((package, func, args, kwargs))

    def pop(self):
        return self._dequeue.popleft()

    def first(self):
        """
        Return the first member of the queue, but do not remove.
        """
        return self._dequeue[0]

    def save(self, file=None):
        file = os.path.abspath(os.path.expanduser(file))
        pickle.dump(self, open(file, "wb"))

    def to_string(self, arg_separator=DEFAULT_ARGUMENT_SEPARATOR, func_separator=DEFAULT_FUNCTION_SEPARATOR):
        """
        :param arg_separator: Separator character to be used between arguments.
        :param func_separator: Separator character to be used between functions.
        """
        out = cStringIO.StringIO()
        for entry in self._dequeue:
            e = map(lambda x: str(x), list(entry))

            out.write(e[0] + DEFAULT_ARGUMENT_SEPARATOR + e[1] + DEFAULT_ARGUMENT_SEPARATOR +
                      e[2] + DEFAULT_ARGUMENT_SEPARATOR + e[3] + DEFAULT_FUNCTION_SEPARATOR)

        return out.getvalue()

    def from_string(self, string, arg_separator=DEFAULT_ARGUMENT_SEPARATOR, func_separator=DEFAULT_FUNCTION_SEPARATOR):
        from_string(string, self, arg_separator, func_separator)
