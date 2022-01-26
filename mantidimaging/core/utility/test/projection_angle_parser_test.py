# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
import tempfile
from contextlib import contextmanager

import numpy as np
import pytest

from mantidimaging.core.utility.projection_angle_parser import ProjectionAngleFileParser


@contextmanager
def tempinput(data):
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(data.encode("ascii"))
    temp.close()
    try:
        yield temp.name
    finally:
        os.unlink(temp.name)


@pytest.mark.parametrize(
    'input',
    ["0,0.1,0.2,0.3,0.4,0.5", "0,0.1,0.2,0.3,0.4,0.5\n", "0\n0.1\n0.2\n0.3\n0.4\n0.5", "0\n0.1\n0.2\n0.3\n0.4\n0.5\n"])
def test_angles_as_csv(input: str):
    expected = np.array([
        0.0, 0.0017453292519943296, 0.003490658503988659, 0.005235987755982988, 0.006981317007977318,
        0.008726646259971648
    ])
    with tempinput(input) as tempfilename:
        pafp = ProjectionAngleFileParser(tempfilename)
        result = pafp.get_projection_angles().value
        np.testing.assert_array_almost_equal(expected, result, err_msg="Arrays not equal")
