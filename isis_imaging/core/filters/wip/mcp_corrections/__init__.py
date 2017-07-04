from __future__ import (absolute_import, division, print_function)

from .mcp_corrections import execute, _cli_register  # noqa:F401

del absolute_import, division, print_function  # noqa:F821

try:
    del mcp_corrections  # noqa:F821
except NameError:
    # this happens if not calling from ipython
    pass
