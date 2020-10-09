import unittest

from mantidimaging.core.utility.registrator import (get_package_children)


class RegistratorTest(unittest.TestCase):
    """This test suite tests the registrator functionality by operating on the
    mantidimaging.core.operations package.

    If any operations are added or removed, or if the structure of that
    package is changed then this test will need to be adjusted
    accordingly.
    """
    def __init__(self, *args, **kwargs):
        super(RegistratorTest, self).__init__(*args, **kwargs)

    def test_get_package_children_modules_only(self):
        modules = get_package_children('mantidimaging.core.operations.wip', packages=False, modules=True)

        modules = list([m[1] for m in modules])

        self.assertEqual(modules, [
            'mantidimaging.core.operations.wip.cut_off.cut_off',
            'mantidimaging.core.operations.wip.cut_off.test.cut_off_test',
            'mantidimaging.core.operations.wip.mcp_corrections.mcp_corrections',
            'mantidimaging.core.operations.wip.outliers_isis.outliers_isis',
            'mantidimaging.core.operations.wip.outliers_isis.test.outliers_isis_test',
        ])

    def test_get_package_children_packages_and_modules(self):
        modules = get_package_children('mantidimaging.core.operations.wip', packages=True, modules=True)

        modules = list([m[1] for m in modules])

        self.assertEqual(modules, [
            'mantidimaging.core.operations.wip.cut_off',
            'mantidimaging.core.operations.wip.cut_off.cut_off',
            'mantidimaging.core.operations.wip.cut_off.test',
            'mantidimaging.core.operations.wip.cut_off.test.cut_off_test',
            'mantidimaging.core.operations.wip.mcp_corrections',
            'mantidimaging.core.operations.wip.mcp_corrections.mcp_corrections',
            'mantidimaging.core.operations.wip.outliers_isis',
            'mantidimaging.core.operations.wip.outliers_isis.outliers_isis',
            'mantidimaging.core.operations.wip.outliers_isis.test',
            'mantidimaging.core.operations.wip.outliers_isis.test.outliers_isis_test',
        ])
