from __future__ import (absolute_import, division, print_function)


def execute(data, minus_log, h):
    if minus_log:
        # import early to check if tool is available
        from recon.tools import importer
        tool = importer.do_importing('tomopy')
        h.pstart("Calculating -log on the sample data.")
        # this check prevents division by 0 errors from the minus_log
        data[data == 0] = 1e-6
        # the operation is done in place
        tool.prep.normalize.minus_log(data, out=data)
        h.pstop("Finished calculating -log on the sample data.")
    else:
        h.tomo_note("Not applying -log.")

    return data