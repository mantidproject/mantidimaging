def execute(data,
            run_ring_removal=False,
            center_x=None,
            center_y=None,
            thresh=300.0,
            thresh_max=300.0,
            thresh_min=-100.0,
            theta_min=30,
            rwidth=30,
            cores=None,
            chunksize=None,
            h=None):
    """
    Removal of ring artifacts in reconstructed volume.

    :param data :: stack of projection images as 3d data (dimensions z, y, x), with
    z different projections angles, and y and x the rows and columns of individual images.

    :param run_ring_removal :: 'wf': Wavelet-Fourier based run_ring_removal

    Returns :: filtered data hopefully without stripes which should dramatically decrease
    ring artifacts after reconstruction and the effect of these on post-processing tasks
    such as segmentation of the reconstructed 3d data volume.
    """
    from helper import Helper
    h = Helper.empty_init() if h is None else h
    if run_ring_removal:
        h.check_data_stack(data)

        from recon.tools import importer
        # tomopy = importer.do_importing('tomopy')
        h.pstart("Starting ring removal...")
        import tomopy.misc.corr
        # FIXME out= is not available in this tomopy, it is available in source though @github
        data = tomopy.misc.corr.remove_ring(
            data,
            center_x=center_x,
            center_y=center_y,
            thresh=thresh,
            thresh_max=thresh_max,
            thresh_min=thresh_min,
            theta_min=theta_min,
            rwidth=rwidth,
            ncore=cores,
            nchunk=chunksize)
        h.pstop("Finished ring removal...")
    else:
        h.tomo_print_note("Not running ring removal.")

    return data
