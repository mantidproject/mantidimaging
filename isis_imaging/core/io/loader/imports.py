from __future__ import absolute_import, division, print_function


def import_pyfits():
    try:
        import pyfits
    except ImportError:
        # In Anaconda python, the pyfits package is in a different place,
        # and this is what you frequently find on windows.
        try:
            import astropy.io.fits as pyfits
        except ImportError:
            raise ImportError(
                "Cannot find the package 'pyfits' which is required to "
                "read/write FITS image files")

    return pyfits


def import_skimage_io():
    """
    To import skimage io only when it is/can be used
    """
    try:
        from skimage import io as skio
        # tifffile works better on local, but not available on scarf
        # no plugin will use the default python imaging library (PIL)
        # This behaviour might need to be changed when switching to python 3
        skio.use_plugin('tifffile')
    except ImportError as exc:
        raise ImportError(
            "Could not find the package skimage, its subpackage "
            "io and the pluging freeimage which are required to support "
            "several image formats. Error details: {0}".format(exc))
    return skio
