from __future__ import absolute_import, division, print_function

import isis_imaging.helper as h
from isis_imaging.core.algorithms import cor_interpolate
from isis_imaging.core.algorithms.shape_splitter import ShapeSplitter
from isis_imaging.core.io import loader


def execute(config, executable):
    """
    The execution splitters allows limitation of the memory usage.

    This is achieved by calculating how we can subset the data so it can be
    processed a subset at a time, without going the maximum allowed memory.

    :param config: The reconstruciton config. Necessary to read the reconstruction parameters.

    :param executable: The function that will be executed.
    """
    recon = config.func.reconstruction if config.func.reconstruction else False

    data_shape = loader.read_in_shape(config)

    shape_splitter = ShapeSplitter(data_shape, 0, config.func.data_dtype,
                                   config.func.max_memory,
                                   config.func.max_ratio, recon)

    split, step = shape_splitter.execute()

    # if we are reconstructing
    if recon:
        # if 0 this will just generate the same for everything
        slices = config.func.cor_slices if config.func.cor_slices is not None else 0
        centers_of_rotation = cor_interpolate.execute(data_shape[0], slices,
                                                      config.func.cors)
        h.tomo_print("Generated cors: {0}".format(centers_of_rotation))

    h.tomo_print_note("Split: {0}, with step: {1}".format(split, step))
    for i in range(len(split) - 1):
        config.func.indices = [split[i], split[i + 1], 1]
        h.tomo_print("Running on indices: {0}".format(config.func.indices))
        if recon:
            config.func.cors = centers_of_rotation[split[i]:split[i + 1]]

        executable(config)

    return split, step
