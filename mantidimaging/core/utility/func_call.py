from __future__ import (absolute_import, division, print_function)

from mantidimaging.core.utility.special_imports import import_inspect


def call_with_known_parameters(func, *args, **kwargs):
    inspect = import_inspect()
    sig = inspect.signature(func)
    params = sig.parameters.keys()
    ka = dict((k, v) for k, v in kwargs.items() if k in params)
    return func(**ka)
