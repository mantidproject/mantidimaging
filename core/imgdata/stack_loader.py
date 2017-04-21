from __future__ import absolute_import, division, print_function

import helper as h


def parallel_move_data(input_data, output_data):
    """
    Forwarded function for parallel loading of data
    :param input_data: shared_data
    :param output_data: second_shared_data
    """
    output_data[:] = input_data[:]


def do_stack_load_seq(data, new_data, img_shape, name):
    """
    Sequential version of loading the data.
    This performs faster locally, but parallel performs faster on SCARF

    :param data: shared array of data
    :param new_data:
    :param img_shape:
    :param name:
    :return: the loaded data
    """
    h.prog_init(img_shape[0], name)
    for i in range(img_shape[0]):
        data[i] = new_data[i]
        h.prog_update()
    h.prog_close()
    return data


def do_stack_load_par(data, new_data, cores, chunksize, name):
    from core.parallel import two_shared_mem as ptsm
    f = ptsm.create_partial(
        parallel_move_data, fwd_function=ptsm.inplace_fwd_func)
    ptsm.execute(new_data, data, f, cores, chunksize, name)
    return data


def execute(load_func,
            file_name,
            dtype,
            name,
            cores=None,
            chunksize=None,
            parallel_load=False,
            indices=None):
    """
    Load a single image FILE that is expected to be a stack of images.

    Parallel execution can be slower depending on the storage system.

    ! On HDD I've found it's about 50% SLOWER, thus not recommended!

    :param file_name :: list of image file paths given as strings
    :param load_func :: file name extension if fixed (to set the expected image format)
    :param dtype :: data type for the output numpy array
    :param cores: Default:1, cores to be used if parallel_load is True
    :param chunksize: chunk of work per worker
    :param parallel_load: Default: False, if set to true the loading of the data will be done in parallel.
            This could be faster depending on the IO system. For local HDD runs the recommended setting is False
    :return: stack of images as a 3-elements tuple: numpy array with sample images, white image, and dark image.
    """
    # create shared array
    from core.parallel import utility as pu
    new_data = load_func(file_name)

    if indices is not None and len(indices) == 2:
        new_data = new_data[indices[0]:indices[1]]

    img_shape = new_data.shape
    data = pu.create_shared_array(img_shape, dtype=dtype)

    if parallel_load:
        return do_stack_load_par(data, new_data, cores, chunksize, name)
    else:
        # we could just move with data[:] = new_data[:] but then we don't get 
        # loading bar information, and I doubt there's any performance gain
        return do_stack_load_seq(data, new_data, img_shape, name)
