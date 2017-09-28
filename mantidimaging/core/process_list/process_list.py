from __future__ import absolute_import, division, print_function

import os
import sys
# using pickle instead of dill, because dill is not available on SCARF
import pickle

from ast import literal_eval
from six import StringIO

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
    Currently only works with MantidImaging internal functions.
    """

    def __init__(self):
        self._list = []
        self._list_idx = 0

    def __str__(self):
        # call with default separators
        return self.to_string(DEFAULT_ARGUMENT_SEPARATOR, '\n')

    def __len__(self):
        return len(self._list)

    def __eq__(self, rhs):
        return self._list == rhs._list

    def __getitem__(self, item):
        return self._list[item]

    def __iter__(self):
        return self

    def is_over(self):
        """
        :return: True if we have traversed all of the list, False otherwise
        """
        return self._list_idx == len(self._list)

    def next(self):
        """
        :return: Return the next function stored in the Process List
        """
        if self.is_over():
            return None
        else:
            f = self._list[self._list_idx]
            self._list_idx += 1
            return f

    def previous(self):
        """
        :return: Return the previous function stored in the Process List
        """
        if self._list_idx == 0:
            return None
        else:
            f = self._list[self._list_idx]
            self._list_idx -= 1
            return f

    def clear(self):
        """
        Clear all contents from the Process List
        """
        self._list = []

    def store(self, func, *args, **kwargs):
        """
        Store a function in the process list to be executed later. The arguments must be literal values.
        Note: More arguments can be appended when the funciton is called for execution.

        :param func: This works with a function reference, because metadata needs to be read from the function.
        :param args: Arguments that will be forwarded to the function. They must be literal values.
        :param kwargs: Keyword arguments that will be forwarded to the function. They must be literal values.
        """
        self._store_func(func, args, kwargs)

    def _store_func(self, func, args, kwargs):
        import mantidimaging.core.algorithms.special_imports as imps
        inspect = imps.import_inspect()
        parameters = inspect.signature(func).parameters
        assert set(kwargs.keys()).issubset(parameters), \
            "One or more of the keyword arguments provided were NOT found in the function's declaration!"

        func_package = func.__globals__['__name__'].rsplit('.', 1)[0]
        func_name = func.__name__
        self._store_string(func_package, func_name, args, kwargs)

    def _store_string(self, package, func, args, kwargs):
        self._list.append((package, func, args, kwargs))

    def first(self):
        """
        Return the first member of the queue, but do not remove.
        """
        return self._list[0]

    def save(self, file=None):
        file = os.path.abspath(os.path.expanduser(file))
        pickle.dump(self, open(file, "wb"))

    def to_string(self, arg_separator=DEFAULT_ARGUMENT_SEPARATOR, func_separator=DEFAULT_FUNCTION_SEPARATOR):
        """
        :param arg_separator: Separator character to be used between arguments.
        :param func_separator: Separator character to be used between functions.
        """
        out = StringIO()
        for entry in self._list:
            e = list(map(lambda x: str(x), list(entry)))

            output_string = e[0] + DEFAULT_ARGUMENT_SEPARATOR + e[1] + DEFAULT_ARGUMENT_SEPARATOR + \
                e[2] + DEFAULT_ARGUMENT_SEPARATOR + e[3] + DEFAULT_FUNCTION_SEPARATOR
            out.write(output_string)

        return out.getvalue()

    def from_string(self, string, arg_separator=DEFAULT_ARGUMENT_SEPARATOR, func_separator=DEFAULT_FUNCTION_SEPARATOR):
        from_string(string, self, arg_separator, func_separator)
