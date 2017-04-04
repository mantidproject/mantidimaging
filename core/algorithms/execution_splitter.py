from __future__ import (absolute_import, division, print_function)


def execute(config, executable):
    from core.imgdata import loader

    data_shape = loader.read_in_shape(config)
    from core.algorithms.shape_splitter import ShapeSplitter
    shape_splitter = ShapeSplitter(data_shape, 0, config.func.data_dtype,
                                   config.func.max_memory,
                                   config.func.max_ratio)
    split, step = shape_splitter.execute()

    # if we are reconstructing
    recon = False
    if config.func.cors:
        recon = True
        # if 0 this will just generate the same for everything
        slices = config.func.cor_slices if config.func.cor_slices is not None else 0
        from core.algorithms import cor_interp
        centers_of_rotation = cor_interp.execute(data_shape[0], slices,
                                                 config.func.cors)
        print("generated cors:", centers_of_rotation)

    print(split, step)
    print("executing the thing")
    for i in range(len(split) - 1):
        config.func.indices = [split[i], split[i + 1]]
        print("Running on indices:", config.func.indices)
        if recon:
            config.func.cors = centers_of_rotation[split[i]:split[i + 1]]

        executable(config)

    return split, step
