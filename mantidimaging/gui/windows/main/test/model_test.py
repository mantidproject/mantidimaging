import unittest

import mock

from mantidimaging.gui.windows.main import MainWindowModel
from mantidimaging.gui.windows.main.model import StackId


class MainWindowModelTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MainWindowModelTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.model = MainWindowModel()
        self.model_class_name = f"{self.model.__module__}.{self.model.__class__.__name__}"
        self.stack_list_property = f"{self.model_class_name}.stack_list"

    def test_initial_stack_list(self):
        self.assertEquals(self.model.stack_names, [])

    def test_create_name_no_stacks_loaded(self):
        # Mock the stack list function (this depends on Qt)
        with mock.patch(self.stack_list_property, new_callable=mock.PropertyMock) as mock_stack_list:
            mock_stack_list.return_value = []
            self.assertEquals(self.model.create_name("test"), "test")

    def test_create_name_one_duplicate_stack_loaded(self):
        with mock.patch(self.stack_list_property, new_callable=mock.PropertyMock) as mock_stack_list:
            mock_stack_list.return_value = [StackId('aaa', 'test')]
            self.assertEquals(self.model.create_name("test"), "test_2")

    def test_create_name_multiple_duplicate_stacks_loaded(self):
        with mock.patch(self.stack_list_property, new_callable=mock.PropertyMock) as mock_stack_list:
            mock_stack_list.return_value = [StackId('aaa', 'test'), StackId('aaa', 'test_2'), StackId('aaa', 'test_3')]
            self.assertEquals(self.model.create_name("test"), "test_4")

    def test_create_name_strips_extension(self):
        with mock.patch(self.stack_list_property, new_callable=mock.PropertyMock) as mock_stack_list:
            mock_stack_list.return_value = []
            self.assertEquals(self.model.create_name("test.tif"), "test")


if __name__ == '__main__':
    unittest.main()
