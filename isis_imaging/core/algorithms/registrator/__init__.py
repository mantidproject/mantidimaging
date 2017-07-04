from __future__ import (absolute_import, division, print_function)

from .registrator import register_into # noqa: F401
from .cli_registrator import cli_register

del absolute_import, division, print_function

"""
Access to `gui_registrator` is more convoluted than `from .gui_registrator import gui_register` because we want to avoid
importing all of the PyQt modules when not using the GUI.
"""