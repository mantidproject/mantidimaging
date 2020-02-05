import unittest
from unittest import mock

import numpy as np

from mantidimaging.core.utility.savu_interop.plugin_list import SAVUPluginListEntry
from mantidimaging.gui.windows.savu_filters.process_list import ProcessListView, ProcessListPresenter


PLUGIN_NAME = "TestPlugin"


class ProcessListPresenterTest(unittest.TestCase):
    def setUp(self):
        view = mock.create_autospec(ProcessListView)
        self.presenter = ProcessListPresenter(view)

    @staticmethod
    def _test_plugin():
        return SAVUPluginListEntry(True, *[np.string_() for _ in range(4)],
                                   name=np.string_(PLUGIN_NAME), user=np.string_())

    def test_add_plugin(self):
        plugin = self._test_plugin()
        self.presenter.add_plugin(plugin)
        self.assertEqual(len(self.presenter.model.plugins), 1, "Model should have a plugin")
        self.assertEqual(self.presenter.model.plugins[0], plugin, "Plugin in model should be the one added")
        self.presenter.view.display_plugin.assert_called_once_with(PLUGIN_NAME)
