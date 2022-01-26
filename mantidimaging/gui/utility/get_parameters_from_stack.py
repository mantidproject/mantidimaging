# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later


def get_parameters_from_stack(stack, params):
    return {k: stack.get_parameter_value(v) for (k, v) in params.items()} if params else {}
