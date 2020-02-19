import importlib


def _import_module(package):
    return importlib.import_module(package.replace('/', '.'))


def execute(entry, *args, **kwargs):
    """
    Execute the stored function in ProcessList.

    Any additional arguments will be appended to the front of the currently
    existing arguments

    :param entry: Tuple with the following structure:
                  (module path, function, args, kwargs)

    :param *args: The arguments to be appended to the back of the currently
                  existing arguments

    :param **kwargs: The keyword arguments to be appended to the back of the
                     currently existing arguments

    :returns: The result from the function that was called
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

    Assumes the first argument passed in the input data.

    Any additional arguments will be appended to the back of the currently
    existing arguments

    :param entry: Tuple with the following structure:
                  (module path, function, args, kwargs)

    :param *args: The arguments to be appended to the back of the currently
                  existing arguments

    :param **kwargs: The keyword arguments to be appended to the back of the
                     currently existing arguments

    :returns: The result from the function that was called
    """
    package = _import_module(entry[0])
    func = entry[1]
    # assume the first parameter is the input data, and append the rest at the
    # end
    args = (args[0], ) + entry[2] + args[1:]
    kwargs.update(entry[3])
    to_call = getattr(package, func)
    return to_call(*args, **kwargs)


def execute_new(entry, *args, **kwargs):
    """
    Execute the stored function in ProcessList.

    The original arguments will be discarded, and only the new ones will be
    used

    :param entry: Tuple with the following structure:
                  (module path, function, args, kwargs)

    :param *args: The arguments to be appended to the back of the currently
                  existing arguments

    :param **kwargs: The keyword arguments to be appended to the back of the
                     currently existing arguments

    :returns: The result from the function that was called
    """
    package = _import_module(entry[0])
    func = entry[1]
    to_call = getattr(package, func)
    return to_call(*args, **kwargs)
