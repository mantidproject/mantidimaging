from __future__ import absolute_import, division, print_function

import importlib


def _import_module(package):
    return importlib.import_module(package.replace('/', '.'))


def execute(entry, *args, **kwargs):
    """
    Execute the stored function in ProcessList.
    Any additional arguments will be appended to the front of the currently existing arguments
    :param
    """
    package = _import_module(entry[0])
    func = entry[1]
    args = args + entry[2]
    kwargs.update(entry[3])

    to_call = getattr(package, func)
    return to_call(*args, **kwargs)


def execute_back(entry, *args, **kwargs):
    """
    Execute the stored function in ProcessList.
    Any additional arguments will be appended to the back of the currently existing arguments
    :param
    """
    package = _import_module(entry[0])
    func = entry[1]
    args = entry[2] + args
    kwargs = entry[3] + kwargs
    to_call = getattr(package, func)
    return to_call(*args, **kwargs)


def execute_new(entry, *args, **kwargs):
    """
    Execute the stored function in ProcessList.
    The original arguments will be discarded, and only the new ones will be used
    """
    package = _import_module(entry[0])
    func = entry[1]
    to_call = getattr(package, func)
    return to_call(*args, **kwargs)
