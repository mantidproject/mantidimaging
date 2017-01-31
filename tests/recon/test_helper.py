from recon.helper import Helper
import numpy as np
import numpy as npt


def gen_img_numpy_rand():
    # generate 10 images with dimensions 10x10, all values 1. float32
    return np.random.rand(10, 10, 10)


def gen_img_shared_array(shape=(10, 10, 10)):
    from parallel import utility as pu
    # generate 10 images with dimensions 10x10, all values 1. float32
    d = pu.create_shared_array(shape)
    n = np.random.rand(shape)

    for i in range(shape[0]):
        d[i] = n[i]

    return d


def assert_equals(thing1, thing2):
    npt.assert_equal(thing1, thing2)


def assert_not_equals(thing1, thing2):
    npt.assert_raises(AssertionError, npt.assert_equal, thing1, thing2)


def copy(source):
    from copy import deepcopy
    return deepcopy(source)


def gimme_helper():
    return Helper.empty_init()
