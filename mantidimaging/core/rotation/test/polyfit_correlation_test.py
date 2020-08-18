import mock
import numpy as np

from mantidimaging.test_helpers.unit_test_helper import generate_images
from ..polyfit_correlation import do_search, get_search_range, find_center
from ...data import Images
from ...utility.progress_reporting import Progress


def test_do_search():
    test_p0 = np.identity(10)
    test_p180 = np.fliplr(test_p0)

    search_range = get_search_range(test_p0.shape[1])
    result = do_search(0, test_p0.shape[1], test_p0, test_p180, search_range)
    assert result == -1, f"Found {result}"


def test_find_center():
    images = generate_images((10, 10, 10))
    images.data[0] = np.identity(10)
    images.proj180deg = Images(np.fliplr(images.data))
    mock_progress = mock.create_autospec(Progress)
    res_cor, res_tilt = find_center(images, mock_progress)
    assert mock_progress.update.call_count == 10
    assert res_cor.value == 5.0, f"Found {res_cor.value}"
    assert res_tilt.value == 0.0, f"Found {res_tilt.value}"
