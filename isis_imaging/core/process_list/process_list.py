from __future__ import absolute_import, division, print_function

# using pickle instead of dill, because dill is not available on SCARF
import pickle
import os
import inspect
import importlib
import cStringIO
from collections import deque

from isis_imaging.core.algorithms import finder


DEFAULT_ARGUMENT_SEPARATOR = ' '
DEFAULT_FUNCTION_SEPARATOR = ';'


def load(file=None):
    return pickle.load(open(file, "rb"))


class ProcessList(object):
    def __init__(self):
        self._list = deque()

    def __str__(self):
        # call with default separators
        return self.to_string(DEFAULT_ARGUMENT_SEPARATOR, DEFAULT_FUNCTION_SEPARATOR)

    def __len__(self):
        return len(self._list)

    def __eq__(self, rhs):
        return self._list == rhs._list

    def store(self, func, *args, **kwargs):
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
        self._list.append((package, func, args, kwargs))

    def pop(self):
        return self._list.popleft()

    def save(self, file=None):
        file = os.path.abspath(os.path.expanduser(file))
        pickle.dump(self, open(file, "wb"))

    def to_string(self, arg_separator=DEFAULT_ARGUMENT_SEPARATOR, func_separator=DEFAULT_FUNCTION_SEPARATOR):
        """
        :param arg_separator: Separator character to be used between arguments.
        :param func_separator: Separator character to be used between functions.
        """
        out = cStringIO.StringIO()
        for entry in self._list:
            e = map(lambda x: str(x), list(entry))

            out.write(e[0] + DEFAULT_ARGUMENT_SEPARATOR + e[1] + DEFAULT_ARGUMENT_SEPARATOR +
                      e[2] + DEFAULT_ARGUMENT_SEPARATOR + e[3] + DEFAULT_FUNCTION_SEPARATOR)
        return out.getvalue()

    def from_string(self, string):
        pass


def execute(data, entry):
    package = importlib.import_module(entry[0].replace('/', '.'))
    func = entry[1]
    args = entry[2]
    kwargs = entry[3]
    to_call = getattr(package, func)
    return to_call(data, *args, **kwargs)
