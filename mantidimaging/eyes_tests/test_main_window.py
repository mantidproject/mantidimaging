from eyes_tests.test_base_eyes import BaseEyesTest


class MainWindowTest(BaseEyesTest):
    def test_main_window_opens(self):
        self.check_target()
