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

    def test_get_package_children(self):
        modules = get_package_children('mantidimaging.core.filters', packages=True)

        modules = list([m[1] for m in modules])

        self.assertEquals(modules, [
            'mantidimaging.core.filters.circular_mask', 'mantidimaging.core.filters.circular_mask.test',
            'mantidimaging.core.filters.clip_values', 'mantidimaging.core.filters.clip_values.test',
            'mantidimaging.core.filters.crop_coords', 'mantidimaging.core.filters.crop_coords.test',
            'mantidimaging.core.filters.cut_off', 'mantidimaging.core.filters.cut_off.test',
            'mantidimaging.core.filters.divide', 'mantidimaging.core.filters.divide.test',
            'mantidimaging.core.filters.flat_fielding', 'mantidimaging.core.filters.flat_fielding.test',
            'mantidimaging.core.filters.gaussian', 'mantidimaging.core.filters.gaussian.test',
            'mantidimaging.core.filters.median_filter', 'mantidimaging.core.filters.median_filter.test',
            'mantidimaging.core.filters.minus_log', 'mantidimaging.core.filters.minus_log.test',
            'mantidimaging.core.filters.outliers', 'mantidimaging.core.filters.outliers.test',
            'mantidimaging.core.filters.rebin', 'mantidimaging.core.filters.rebin.test',
            'mantidimaging.core.filters.ring_removal', 'mantidimaging.core.filters.ring_removal.test',
            'mantidimaging.core.filters.roi_normalisation', 'mantidimaging.core.filters.roi_normalisation.test',
            'mantidimaging.core.filters.rotate_stack', 'mantidimaging.core.filters.rotate_stack.test',
            'mantidimaging.core.filters.stripe_removal', 'mantidimaging.core.filters.stripe_removal.test',
            'mantidimaging.core.filters.wip', 'mantidimaging.core.filters.wip.mcp_corrections'
        ])

    def test_get_package_children_with_ignores(self):
        modules = get_package_children('mantidimaging.core.filters',
                                       packages=True,
                                       ignore=['mantidimaging.core.filters.wip', 'test'])

        modules = list([m[1] for m in modules])

        self.assertEquals(modules, [
            'mantidimaging.core.filters.circular_mask', 'mantidimaging.core.filters.clip_values',
            'mantidimaging.core.filters.crop_coords', 'mantidimaging.core.filters.cut_off',
            'mantidimaging.core.filters.divide', 'mantidimaging.core.filters.flat_fielding',
            'mantidimaging.core.filters.gaussian', 'mantidimaging.core.filters.median_filter',
            'mantidimaging.core.filters.minus_log', 'mantidimaging.core.filters.outliers',
            'mantidimaging.core.filters.rebin', 'mantidimaging.core.filters.ring_removal',
            'mantidimaging.core.filters.roi_normalisation', 'mantidimaging.core.filters.rotate_stack',
            'mantidimaging.core.filters.stripe_removal'
        ])

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
