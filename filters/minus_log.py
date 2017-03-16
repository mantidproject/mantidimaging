from __future__ import (absolute_import, division, print_function)
import helper as h


def execute(data, minus_log):
    if minus_log:
        # import early to check if tomopy is available
        from recon.tools import importer
        tomopy = importer.do_importing('tomopy')
        h.pstart("Calculating -log on the sample data.")
        # this check prevents division by 0 errors from the minus_log
        data[data == 0] = 1e-6
        # the operation is done in place
        tomopy.prep.normalize.minus_log(data, out=data)
        h.pstop("Finished calculating -log on the sample data.")

    return data