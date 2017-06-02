from __future__ import absolute_import, division, print_function

from isis_imaging.core.algorithms import cor_interpolate
from isis_imaging.core.algorithms.shape_splitter import ShapeSplitter
from isis_imaging.core.imgdata import loader


def execute(config, executable):

    data_shape = loader.read_in_shape(config)
    shape_splitter = ShapeSplitter(data_shape, 0, config.func.data_dtype,
                                   config.func.max_memory,
                                   config.func.max_ratio, config.func.no_recon)

    split, step = shape_splitter.execute()

    # if we are reconstructing
    recon = False
    if config.func.cors:
        recon = True
        # if 0 this will just generate the same for everything
        slices = config.func.cor_slices if config.func.cor_slices is not None else 0
        centers_of_rotation = cor_interpolate.execute(data_shape[0], slices,
                                                      config.func.cors)
        print("Generated cors:", centers_of_rotation)

    print(split, step)
    for i in range(len(split) - 1):
        config.func.indices = [split[i], split[i + 1], 1]
        print("Running on indices:", config.func.indices)
        if recon:
            config.func.cors = centers_of_rotation[split[i]:split[i + 1]]

        executable(config)

    return split, step
