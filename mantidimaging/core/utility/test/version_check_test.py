# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import mock
import pytest
from mock import DEFAULT

from mantidimaging.core.utility.version_check import (_do_version_check, _make_version_str, _parse_version,
                                                      check_version_and_label)


def test_parse_version():
    parsed = _parse_version("9.9.9_1234")

    assert parsed.version == (9, 9, 9)
    assert parsed.commits == 1234


def test_make_version_str():
    input_version_str = "9.9.9_1234"
    parsed = _parse_version(input_version_str)

    version_string = _make_version_str(parsed)

    assert version_string == input_version_str


@pytest.mark.parametrize(
    'old, new, should_call_back, is_main_label',
    [
        ["9.9.9_1234", "19.9.9_1234", True, True],  # remote is newer
        ["9.9.9_1234", "9.9.9_1234", False, True],  # local and remote is the same
        ["19.9.9_1234", "9.9.9_1234", False, True],  # for some reason the local is newer
        ["9.9.9_1234", "19.9.9_1234", True, False],  # remote is newer
        ["9.9.9_1234", "9.9.9_1234", False, False],  # local and remote is the same
        ["19.9.9_1234", "9.9.9_1234", False, False],  # for some reason the local is newer
    ])
@mock.patch("mantidimaging.core.utility.version_check.LOG")
def test_do_version_check_main(mock_log, old: str, new: str, should_call_back: bool, is_main_label: bool):
    older = _parse_version(old)
    newer = _parse_version(new)

    callback_mock = mock.Mock()

    def callback(msg):
        callback_mock(msg)

    _do_version_check(older, newer, callback, is_main_label)

    # True when local is older
    if should_call_back:
        callback_mock.assert_called_once()
        # when local is older the LOG sends more info messages
        assert mock_log.info.call_count == 2

        # last call has the install command
        # just check that certain things are in it
        logged_update_message = mock_log.info.mock_calls[-1].args[0]
        assert "source /opt/miniconda/bin/activate /opt/miniconda" in logged_update_message
        assert "https://raw.githubusercontent.com/mantidproject/mantidimaging/master/install.sh" \
               in logged_update_message

        if is_main_label:
            # when main this should NOT be in the string
            assert "ENVIRONMENT_NAME=mantidimaging_unstable REPO_LABEL=unstable" not in logged_update_message
        else:
            assert "ENVIRONMENT_NAME=mantidimaging_unstable REPO_LABEL=unstable" in logged_update_message
    else:
        callback_mock.assert_not_called()
        assert mock_log.info.call_count == 1
        logged_update_message = mock_log.info.mock_calls[-1].args[0]
        assert "Running the latest Mantid Imaging" in logged_update_message


@mock.patch.multiple("mantidimaging.core.utility.version_check", subprocess=DEFAULT, requests=DEFAULT, LOG=DEFAULT)
def test_check_version_and_label_empty_local(subprocess=None, requests=None, LOG=None):
    subprocess.check_output.return_value = b""
    callback_mock = mock.Mock()

    def callback(msg):
        callback_mock(msg)

    assert False is check_version_and_label(callback)
    assert LOG.info.call_count == 2
    requests.get.assert_not_called()


@mock.patch.multiple("mantidimaging.core.utility.version_check",
                     subprocess=DEFAULT,
                     requests=DEFAULT,
                     LOG=DEFAULT,
                     json=DEFAULT)
def test_check_version_and_label_remote_get_raises(subprocess=None, requests=None, LOG=None, json=None):
    subprocess.check_output.return_value = b"1.1.0_1018 mantid/label/unstable"
    json.loads.return_value = {"latest_version": "1.1.0_1018", "versions": ['1.1.0_1090']}
    requests.get.side_effect = RuntimeError

    callback_mock = mock.Mock()

    def callback(msg):
        callback_mock(msg)

    assert check_version_and_label(callback) is False
    assert LOG.info.call_count == 2

    logged_update_message = LOG.info.mock_calls[-1].args[0]
    assert "Could not connect to Anaconda remote" in logged_update_message

    requests.get.assert_called_once()


@mock.patch.multiple("mantidimaging.core.utility.version_check",
                     subprocess=DEFAULT,
                     requests=DEFAULT,
                     LOG=DEFAULT,
                     json=DEFAULT)
def test_check_version_and_label_unstable_remote_newer(subprocess=None, requests=None, LOG=None, json=None):
    subprocess.check_output.return_value = b"1.1.0_1018 mantid/label/unstable"
    json.loads.return_value = {"latest_version": "1.1.0_1018", "versions": ['1.1.0_1090']}

    callback_mock = mock.Mock()

    def callback(msg):
        callback_mock(msg)

    assert check_version_and_label(callback) is False

    requests.get.assert_called_once()
    assert LOG.info.call_count == 3
    logged_update_message = LOG.info.mock_calls[-1].args[0]
    assert "source /opt/miniconda/bin/activate /opt/miniconda" in logged_update_message
    assert "https://raw.githubusercontent.com/mantidproject/mantidimaging/master/install.sh" \
           in logged_update_message

    assert "ENVIRONMENT_NAME=mantidimaging_unstable REPO_LABEL=unstable" in logged_update_message


@mock.patch.multiple("mantidimaging.core.utility.version_check",
                     subprocess=DEFAULT,
                     requests=DEFAULT,
                     LOG=DEFAULT,
                     json=DEFAULT)
def test_check_version_and_label_unstable_remote_same(subprocess=None, requests=None, LOG=None, json=None):
    subprocess.check_output.return_value = b"1.1.0_1090 mantid/label/unstable"
    json.loads.return_value = {"latest_version": "1.1.0_1018", "versions": ['1.1.0_1090']}

    callback_mock = mock.Mock()

    def callback(msg):
        callback_mock(msg)

    assert check_version_and_label(callback) is False

    requests.get.assert_called_once()
    assert LOG.info.call_count == 2
    logged_update_message = LOG.info.mock_calls[-1].args[0]
    assert "Running the latest Mantid Imaging" in logged_update_message


@mock.patch.multiple("mantidimaging.core.utility.version_check",
                     subprocess=DEFAULT,
                     requests=DEFAULT,
                     LOG=DEFAULT,
                     json=DEFAULT)
def test_check_version_and_label_main_remote_newer(subprocess=None, requests=None, LOG=None, json=None):
    subprocess.check_output.return_value = b"1.1.0_1018 mantid/label/main"
    json.loads.return_value = {"latest_version": "1.1.0_1025", "versions": ['1.1.0_1090']}

    callback_mock = mock.Mock()

    def callback(msg):
        callback_mock(msg)

    assert check_version_and_label(callback) is True

    requests.get.assert_called_once()
    assert LOG.info.call_count == 3
    logged_update_message = LOG.info.mock_calls[-1].args[0]
    assert "source /opt/miniconda/bin/activate /opt/miniconda" in logged_update_message
    assert "https://raw.githubusercontent.com/mantidproject/mantidimaging/master/install.sh" \
           in logged_update_message

    # main label shouldn't include this
    assert "ENVIRONMENT_NAME=mantidimaging_unstable REPO_LABEL=unstable" not in logged_update_message


@mock.patch.multiple("mantidimaging.core.utility.version_check",
                     subprocess=DEFAULT,
                     requests=DEFAULT,
                     LOG=DEFAULT,
                     json=DEFAULT)
def test_check_version_and_label_main_remote_same(subprocess=None, requests=None, LOG=None, json=None):
    subprocess.check_output.return_value = b"1.1.0_1018 mantid/label/main"
    json.loads.return_value = {"latest_version": "1.1.0_1018", "versions": ['1.1.0_1090']}

    callback_mock = mock.Mock()

    def callback(msg):
        callback_mock(msg)

    assert check_version_and_label(callback) is True

    requests.get.assert_called_once()
    assert LOG.info.call_count == 2
    logged_update_message = LOG.info.mock_calls[-1].args[0]
    assert "Running the latest Mantid Imaging" in logged_update_message
