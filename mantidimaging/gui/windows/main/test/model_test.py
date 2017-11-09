import unittest

from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.windows.main import MainWindowModel

mock = import_mock()


class MainWindowModelTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(MainWindowModelTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.model = MainWindowModel(None)

    def test_initial_stack_list(self):
        self.assertEquals(self.model.stack_names(),
                          [])

    def test_create_name_no_stacks_loaded(self):
        # Mock the stack list function (this depends on Qt)
        self.model.stack_list = mock.MagicMock(return_value=[])

        self.assertEquals(self.model.create_name("test"),
                          "test")

    def test_create_name_one_duplicate_stack_loaded(self):
        # Mock the stack list function (this depends on Qt)
        self.model.stack_list = mock.MagicMock(return_value=[
            ('aaa', 'test')
        ])

        # Fake items in the active stacks list (required to trigger a check
        # when returning stack lists)
        self.model.active_stacks = [0]

        self.assertEquals(self.model.create_name("test"),
                          "test_2")

    def test_create_name_multiple_duplicate_stacks_loaded(self):
        # Mock the stack list function (this depends on Qt)
        self.model.stack_list = mock.MagicMock(return_value=[
            ('aaa', 'test'),
            ('aaa', 'test_2'),
            ('aaa', 'test_3')
        ])

        # Fake items in the active stacks list (required to trigger a check
        # when returning stack lists)
        self.model.active_stacks = [0]

        self.assertEquals(self.model.create_name("test"),
                          "test_4")

    def test_create_name_strips_extension(self):
        # Mock the stack list function (this depends on Qt)
        self.model.stack_list = mock.MagicMock(return_value=[])

        self.assertEquals(self.model.create_name("test.tif"),
                          "test")


if __name__ == '__main__':
    unittest.main()
