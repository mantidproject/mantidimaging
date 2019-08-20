import importlib
from logging import getLogger
from types import ModuleType

pydevd = importlib.import_module("pydevd")
LOG = getLogger(__name__)

if pydevd is None:
    def reload(module):
        LOG.debug("Not reloading module as pydevd is not available")
        return module
else:
    from _pydevd_bundle.pydevd_reload import xreload

    def reload(module):
        """Recursively reload a module and all its submodules.
        Graph DFS strategy modified from
        https://stackoverflow.com/questions/15506971/recursive-version-of-reload
        """
        visited = set()

        def visit(m):
            if m in visited:
                return
            visited.add(m)

            try:
                xreload(m)
            except RuntimeError:
                LOG.debug(f"Skipping import of {m} as it forbids reloading.")
                # module may not be allowed to be reloaded, such as numpy._globals
                return  # to the level above

            for attribute_name in dir(m):
                attribute = getattr(m, attribute_name)

                if type(attribute) is ModuleType:
                    visit(attribute)

        visit(module)

        return module
