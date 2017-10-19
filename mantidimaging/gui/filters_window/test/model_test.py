import unittest

from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.filters_window import FiltersWindowModel

mock = import_mock()


class FiltersWindowModelTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FiltersWindowModelTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.model = FiltersWindowModel(None)

    def test_filters_populated(self):
        self.assertTrue(len(self.model.filter_names) > 0)

if __name__ == '__main__':
    unittest.main()
