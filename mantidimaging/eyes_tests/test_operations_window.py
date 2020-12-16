from eyes_tests.base_eyes import BaseEyesTest


class OperationsWindowTest(BaseEyesTest):
    def test_operation_window_opens(self):
        self.imaging.show_filters_window()
        self.check_target(widget=self.imaging.filters)
