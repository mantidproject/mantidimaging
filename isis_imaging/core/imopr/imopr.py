from __future__ import (absolute_import, division, print_function)


def get_available_operators():
    return [
        'recon', 'sino', 'show', 'vis', 'cor', 'corvo', 'corpc', 'corwrite',
        'sum', '+', 'subtract', 'sub', '-', 'divide', 'div', '/', 'multiply',
        'mul', '*', 'mean', 'avg', 'x'
    ]


def execute(config):
    """
    Execute the image operator. This allows performing operations on single images, or specified images slices.

    Currently available modes:
        - cor - get the COR for a slice or multiple slices using tomopy find_center. 
            Usages:
                 --imopr <end> cor  # only a single slice will be executed
                 --imopr <start> <end> cor  # step will automatically be 1
                 --imopr <start> <end> <step> cor
        - corwrite - get the COR for a slice or multiple slices using. 
                     Output path is MANDATORY. The reconstructed slices will be 
                     written in subfolders with their index as name.
            Usages:
                 --imopr <end> cor  # only a single slice will be executed
                 --imopr <start> <end> cor  # step will automatically be 1
                 --imopr <start> <end> <step> cor

        TODO outdated:
        - recon - do a reconstruction on a single or multiple slices, --imopr 1 recon, --imopr 10 34 recon
        - sino - visualise the sinogram for single or multiple slices, --imopr 1 sino, --imopr 10 34 sino
        - vis - just visualise the single or multiple images, --imopr 1 vis, --imopr 10 34 vis
        - corvo - get the COR for a slice or multiple slices using
                  tomopy find_center_vo, --imopr 1 corvo, --imopr 10 34 corvo
        - corpc - get the COR for a slice or multiple slices using
                  tomopy find_center_pc, --imopr 1 corpc, --imopr 10 34 corpc
        - opr - do operations on 2 images, that can be:
                sum(also +), --imopr 1 3 sum, --imopr 10 34 +
                subtract(also sub, -), --imopr 1 3 sub, --imopr 10 34 -
                divide(also div, /), --imopr 1 3 div, --imopr 10 34 /
                multiply(also mul, *), --imopr 1 3 mul, --imopr 10 34 *
                mean(also avg, x), --imopr 1 3 avg, --imopr 10 34 x

    COR functions reference: http://tomopy.readthedocs.io/en/latest/api/tomopy.recon.rotation.html

    :param config:
    :return:
    """
    # use [:] to get a copy of the list
    commands = config.func.imopr[:]
    # strip the last command, it must be the name of the package
    package = get_function(commands.pop())
    # the rest is a list of indices
    indices = [int(c) for c in commands]
    config.func.indices = indices

    import helper as h
    h.check_config_integrity(config)
    package.sanity_checks(config)

    from core.imgdata import loader
    sample = loader.load_data(config)
    # the [:] is necessary to get the actual data and not just the nxs header
    # sample = loader.nxsread(config.func.input_path)[:]

    h.tomo_print("Data shape {0}".format(sample.shape))
    flat = dark = None

    # from core.recon.recon import pre_processing
    # sample, flat, dark = pre_processing(config, sample, flat, dark)
    return package.execute(sample, flat, dark, config, indices)


def get_function(package_name):
    if package_name == "recon":
        from core.imopr import recon
        return recon
    elif package_name == "sino":
        from core.imopr import sinogram
        return sinogram
    elif package_name == "show" or package_name == "vis":
        from core.imopr import visualiser
        return visualiser
    elif package_name == "cor":
        from core.imopr import cor
        return cor
    elif package_name == "corvo":
        from core.imopr import corvo
        return corvo
    elif package_name == "corpc":
        from core.imopr import corpc
        return corpc
    elif package_name == "corwrite":
        from core.imopr import corwrite
        return corwrite
    else:
        from core.imopr import opr
        if package_name in opr.get_available_operators():
            return opr
