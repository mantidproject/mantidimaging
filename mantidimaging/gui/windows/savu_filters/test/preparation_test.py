import re
import unittest
from typing import List
from unittest import mock

from mantidimaging.core.configs.savu_backend_docker import (RemoteConfig, RemoteConstants)
from mantidimaging.gui.windows.savu_filters.preparation import (NO_DOCKER_EXE_MESSAGE, prepare_backend)

PLUGIN_NAME = "TestPlugin"


class PreparationTest(unittest.TestCase):
    def assert_list_contains(self, what: str, list: List[str]):
        for item in list:
            if what in item:
                return True
        raise AssertionError(f"{what} was not contained inside any of the lists' members.")

    @mock.patch('mantidimaging.gui.windows.savu_filters.preparation.is_exe', return_value=False)
    def test_docker_not_found_gives_empty_process(self, mock_is_exe):
        process = prepare_backend()

        self.assertIsNone(process.docker_exe)
        # escapes the brackets inside the message, so they don't count as a regex group
        # the \ are doubled to prevent a flake8 warning
        regex = re.compile(NO_DOCKER_EXE_MESSAGE.format(".*").replace("(", "\\(").replace(")", "\\)"))
        self.assertRegex(process.failure_reason, regex)

    some_executable = 'some_executable'

    @mock.patch('mantidimaging.gui.windows.savu_filters.preparation.find_docker', return_value=some_executable)
    def test_docker_found(self, mock_find_docker):
        process = prepare_backend()

        self.assertEquals(process.docker_exe, self.some_executable)

        self.assert_list_contains(RemoteConfig.LOCAL_DATA_DIR, process.args)
        self.assert_list_contains(RemoteConstants.DATA_DIR, process.args)
        self.assert_list_contains(RemoteConfig.LOCAL_OUTPUT_DIR, process.args)
        self.assert_list_contains(RemoteConstants.OUTPUT_DIR, process.args)
        self.assert_list_contains(RemoteConfig.IMAGE_NAME, process.args)

    @mock.patch('mantidimaging.gui.windows.savu_filters.preparation.find_docker', return_value=some_executable)
    def test_docker_found_with_nvidia_runtime(self, mock_find_docker):
        RemoteConfig.NVIDIA_RUNTIME["active"] = True

        process = prepare_backend()

        self.assertEquals(process.docker_exe, self.some_executable)

        self.assert_list_contains(RemoteConfig.NVIDIA_RUNTIME["value"], process.args)
