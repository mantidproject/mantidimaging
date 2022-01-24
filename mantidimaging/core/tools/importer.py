# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later


def do_importing(tool, alg='fbp'):
    """
    The main importing function.

    Does the decision on which tool to import based on the input.

    :param tool: The name of the tool to be imported

    :param alg: The algorithm that will be used. This is only done the ensure
                that it is actually supported.
                If no algorithm is provided, the default is 'fbp', because it's
                supported by all tools.

    :return: the tool reference
    """
    if not isinstance(tool, str):
        raise TypeError("The name of a reconstruction tool is required as a string. " "Got: {0}".format(tool))
    if 'tomopy' == tool:
        from mantidimaging.core.tools.tomopy_tool import TomoPyTool
        TomoPyTool.check_algorithm_compatibility(alg)
        imported_tool = TomoPyTool()
    else:
        raise ValueError("Tried to import unknown tool: {0}".format(tool))

    return imported_tool
