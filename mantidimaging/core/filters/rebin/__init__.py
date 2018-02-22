NAME = 'Rebin'

from .rebin import execute, modes, _cli_register  # noqa:F401
from .rebin_gui import _gui_register  # noqa: F401

del absolute_import, division, print_function  # noqa:F821
