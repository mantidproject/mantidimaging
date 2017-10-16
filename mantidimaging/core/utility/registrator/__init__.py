from __future__ import (absolute_import, division, print_function)

from .registrator import (  # noqa: F401
        find_package_path,
        get_child_modules,
        import_modules,
        register_modules_into
    )

del absolute_import, division, print_function

"""
Access to `gui_registrator` is more convoluted than `from .gui_registrator
import gui_register` because we want to avoid importing all of the PyQt modules
when not using the GUI.
"""
