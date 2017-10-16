from __future__ import (absolute_import, division, print_function)

NAME = 'Remove Outliers'

from .outliers import execute, modes, _cli_register  # noqa:F401
from .outliers_gui import _gui_register  # noqa: F401

del absolute_import, division, print_function  # noqa:F821
