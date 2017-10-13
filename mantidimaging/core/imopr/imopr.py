from __future__ import absolute_import, division, print_function

from logging import getLogger

from mantidimaging import helper as h
from mantidimaging.core.io import loader


def get_available_operators():
    return [
        'recon', 'sino', 'show', 'vis', 'cor', 'corvo', 'corpc', 'corwrite',
        'sum', '+', 'subtract', 'sub', '-', 'divide', 'div', '/', 'multiply',
        'mul', '*', 'mean', 'avg', 'x'
    ]


def execute(config):
    """
    Execute the image operator.

    This allows performing operations on single images, or specified images
    slices.

    This mode respects --indices <start> <stop> <step>.

    This means the operations will be performed only on the indices you have
    specified.

    Currently available modes, more information in each module's file:
        - cor - get the COR for a slice or multiple slices using tomopy
                find_center.
        - corwrite - output a reconstructed image for different CORs for
                     slices.

        TODO outdated:
        - recon - do a reconstruction on a single or multiple slices, --imopr 1
                  recon, --imopr 10 34 recon
        - sino - visualise the sinogram for single or multiple slices, --imopr
                 1 sino, --imopr 10 34 sino
        - vis - just visualise the single or multiple images, --imopr 1 vis,
                --imopr 10 34 vis
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

    COR functions reference:
    http://tomopy.readthedocs.io/en/latest/api/tomopy.recon.rotation.html

    :param config:
    :return:
    """
    # use [:] to get a copy of the list
    commands = config.func.imopr[:]
    # strip the last command, it must be the name of the module
    module = get_function(commands.pop())
    # the rest is a list of indices
    indices = [int(c) for c in commands]

    h.check_config_integrity(config)
    module.sanity_checks(config)

    images = loader.load_from_config(config)

    getLogger(__name__).info(
            "Data shape {0}".format(images.get_sample().shape))

    return module.execute(
            images.get_sample(), images.get_flat(), images.get_dark(),
            config, indices)


def get_function(module_name):
    if module_name == "recon":
        from mantidimaging.core.imopr import recon
        return recon
    elif module_name == "sino":
        from mantidimaging.core.imopr import sinogram
        return sinogram
    elif module_name == "show" or module_name == "vis":
        from mantidimaging.core.imopr import visualiser
        return visualiser
    elif module_name == "cor":
        from mantidimaging.core.imopr import cor
        return cor
    elif module_name == "corvo":
        from mantidimaging.core.imopr import corvo
        return corvo
    elif module_name == "corpc":
        from mantidimaging.core.imopr import corpc
        return corpc
    elif module_name == "corwrite":
        from mantidimaging.core.imopr import corwrite
        return corwrite
    else:
        from mantidimaging.core.imopr import opr
        if module_name in opr.get_available_operators():
            return opr
