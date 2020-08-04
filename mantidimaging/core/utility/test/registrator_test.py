import unittest

from mantidimaging.core.utility.registrator import (get_package_children)


class RegistratorTest(unittest.TestCase):
    """
    This test suite tests the registrator functionality by operating on the
    mantidimaging.core.filters package.

    If any filters are added or removed, or if the structure of that package is
    changed then this test will need to be adjusted accordingly.
    """
    def __init__(self, *args, **kwargs):
        super(RegistratorTest, self).__init__(*args, **kwargs)

    def test_get_package_children_modules_only(self):
        modules = get_package_children('mantidimaging.core.filters.wip', packages=False, modules=True)

        modules = list([m[1] for m in modules])

        self.assertEquals(modules, ['mantidimaging.core.filters.wip.mcp_corrections.mcp_corrections'])

    def test_get_package_children_packages_and_modules(self):
        modules = get_package_children('mantidimaging.core.filters.wip', packages=True, modules=True)

        modules = list([m[1] for m in modules])

        self.assertEquals(modules, [
            'mantidimaging.core.filters.wip.mcp_corrections',
            'mantidimaging.core.filters.wip.mcp_corrections.mcp_corrections'
        ])
