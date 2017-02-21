def execute(data, method=False, cores=None, chunksize=None,
            h=None):
    """
    Removal of ring artifacts in reconstructed volume.

    :param data :: stack of projection images as 3d data (dimensions z, y, x), with
    z different projections angles, and y and x the rows and columns of individual images.

    :param method :: 'wf': Wavelet-Fourier based method

    Returns :: filtered data hopefully without stripes which should dramatically decrease
    ring artifacts after reconstruction and the effect of these on post-processing tasks
    such as segmentation of the reconstructed 3d data volume.
    """
    if method:
        from helper import Helper
        h = Helper.empty_init() if h is None else h
        h.check_data_stack(data)

        from recon.tools import importer
        # tomopy = importer.do_importing('tomopy')
        h.pstart("Starting ring removal...")
        import tomopy.misc.corr
        # FIXME out= is not available in this tomopy, it is available in source though @github
        data[:] = tomopy.misc.corr.remove_ring(data,
                                               center_x=300,
                                               center_y=271,
                                               thresh=300.0,
                                               thresh_max=400.0,
                                               thresh_min=200,
                                               theta_min=30,
                                               rwidth=10, ncore=cores, nchunk=chunksize)
        h.pstop("Finished ring removal...")

    return data
