import numpy as np
_available_operators = {
    'sum': np.sum,
    'sub': np.subtract,
    'subtract': np.subtract,
    'mul': np.multiply,
    'multiply': np.multiply,
    'div': np.true_divide,
    'divide': np.true_divide
}


def get_available_operators():
    return _available_operators.keys()


def execute(sample, flat, dark, config, indices):
    opr = config.func.imopr

    from imopr import helper
    helper.print_start("Running IMOPR with operation {0}".format(opr))

    i1, i2 = helper.handle_indices(indices)

    from imopr import visualiser as vis
    res = _available_operators[opr](sample[i1], sample[i2])

    vis.show_image(res)

    return res