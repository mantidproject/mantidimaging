import sys
import unittest

from PyQt5 import Qt

from mantidimaging.gui.windows.savu_filters.process_list import ProcessListView

app = Qt.QApplication(sys.argv)
PLUGIN_NAME_1 = "TestPlugin"
PLUGIN_NAME_2 = "TestPlugin2"


class ProcessListViewTest(unittest.TestCase):
    def setUp(self):
        self.view = ProcessListView(None)

    def _get_plugin_widget(self, n):
        return self.view.processing_plugins_layout.itemAt(n).widget()

    def test_plugins_labelled_correctly(self):
        self.view.display_plugin(PLUGIN_NAME_1)
        self.view.display_plugin(PLUGIN_NAME_2)

        def get_button_text(plugin_widget):
            return plugin_widget.layout().itemAt(1).widget().text()

        self.assertEqual(self._get_plugin_widget(0).pos_label.text(), "1")
        self.assertEqual(self._get_plugin_widget(1).pos_label.text(), "2")
        self.assertEqual(get_button_text(self._get_plugin_widget(0)), PLUGIN_NAME_1)
        self.assertEqual(get_button_text(self._get_plugin_widget(1)), PLUGIN_NAME_2)

    def test_movement_button_states(self):
        self.view.display_plugin(PLUGIN_NAME_1)
        self.assertEqual(self._get_plugin_widget(0).up_button.isEnabled(), False)
        self.assertEqual(self._get_plugin_widget(0).down_button.isEnabled(), False)

        self.view.display_plugin(PLUGIN_NAME_1)
        self.assertEqual(self._get_plugin_widget(0).up_button.isEnabled(), False)
        self.assertEqual(self._get_plugin_widget(0).down_button.isEnabled(), True)
        self.assertEqual(self._get_plugin_widget(1).up_button.isEnabled(), True)
        self.assertEqual(self._get_plugin_widget(1).down_button.isEnabled(), False)

        self.view.display_plugin(PLUGIN_NAME_1)
        self.assertEqual(self._get_plugin_widget(0).up_button.isEnabled(), False)
        self.assertEqual(self._get_plugin_widget(0).down_button.isEnabled(), True)
        self.assertEqual(self._get_plugin_widget(1).up_button.isEnabled(), True)
        self.assertEqual(self._get_plugin_widget(1).down_button.isEnabled(), True)
        self.assertEqual(self._get_plugin_widget(2).up_button.isEnabled(), True)
        self.assertEqual(self._get_plugin_widget(2).down_button.isEnabled(), False)

    def test_remove_plugin_only_plugin(self):
        self.view.display_plugin(PLUGIN_NAME_1)
        self.view.remove_plugin(0)
        self.assertEqual(len(self.view.plugin_widgets), 0)
        with self.assertRaises(AttributeError):
            self._get_plugin_widget(0)

    def test_remove_plugin_movement_arrows_correct(self):
        self.view.display_plugin(PLUGIN_NAME_1)
        self.view.display_plugin(PLUGIN_NAME_1)
        self.view.display_plugin(PLUGIN_NAME_1)
        self.view.remove_plugin(0)
        self.assertEqual(len(self.view.plugin_widgets), 2)
        self.assertEqual(self._get_plugin_widget(0).up_button.isEnabled(), False)
        self.assertEqual(self._get_plugin_widget(0).down_button.isEnabled(), True)
        self.assertEqual(self._get_plugin_widget(1).up_button.isEnabled(), True)
        self.assertEqual(self._get_plugin_widget(1).down_button.isEnabled(), False)
