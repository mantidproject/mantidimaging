from eyes_tests.base_eyes import BaseEyesTest


class MainWindowTest(BaseEyesTest):
    def test_main_window_opens(self):
        self.check_target()

    def test_main_window_file_menu(self):
        self.show_menu(self.imaging, self.imaging.menuFile)
        self.check_target(widget=self.imaging.menuFile)

    def test_main_window_file_menu_image_loaded(self):
        pass
    
    def test_main_window_help_menu(self):
        self.show_menu(self.imaging, self.imaging.menuHelp)
        self.check_target(widget=self.imaging.menuHelp)

    def test_main_window_loaded_data(self):
        pass
