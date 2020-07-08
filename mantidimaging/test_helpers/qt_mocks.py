from unittest.mock import Mock


class MockQSpinBox:
    def __init__(self, return_value: float):
        self.value = Mock(return_value=return_value)


class MockQComboBox:
    def __init__(self, currentText: str):
        self.currentText = Mock(return_value=currentText)
