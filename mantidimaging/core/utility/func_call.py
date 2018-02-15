from __future__ import (absolute_import, division, print_function)

import inspect


def call_with_known_parameters(func, *args, **kwargs):
    sig = inspect.signature(func)
    params = sig.parameters.keys()
    ka = dict((k, v) for k, v in kwargs.items() if k in params)
    return func(**ka)
