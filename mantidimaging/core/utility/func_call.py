# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import inspect


def call_with_known_parameters(func, **kwargs):
    sig = inspect.signature(func)
    params = sig.parameters.keys()
    ka = dict((k, v) for k, v in kwargs.items() if k in params)
    return func(**ka)
