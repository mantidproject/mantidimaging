=====================
Imaging Changes
=====================

.. contents:: Table of Contents
   :local:

Supported Image Formats
###################################################

Functionality
###################################################

Aggregate
---------
Related command line arguments:
  **--aggregate <start> <end> <method {sum, avg}>**
                        Aggregate image energy levels.

  **--aggregate-angles 0 10**
                        Select which angles to be aggregated with --aggregate.
                        This can be used to spread out the load on multiple nodes.
                        This is inclusive. --aggregate-angles 0 10 will aggregate 0 and 10 included.
                        
  **--aggregate-single-folder-output**
                        The output will be images with increasing number in a single folder.


Convert
-------
Related command line arguments:
  --convert             Convert images to a different format.
  --convert-prefix CONVERT_PREFIX
                        Convert images to a different format.

Imopr
-----
  --imopr [IMOPR [IMOPR ...]]
                        Image operator currently supports a the following operators: ['recon', 'sino', 'show', 'vis', 'cor', 'corvo', 'corpc', 'corwrite', 'sum', '+', 'subtract', 'sub', '-', 'divide', 'div', '/', 'multiply', 'mul', '*', 'mean', 'avg', 'x']

Recon
-----
 
Run Modes:

  -d, --debug           Run debug to specified port, if no port is specified, it will default to 59003
  -p DEBUG_PORT, --debug-port DEBUG_PORT
                        Port on which a debugger is listening.

Reconstruction options:
  -t {tomopy,astra}, --tool {tomopy,astra}
                        Tomographic reconstruction tool to use.
                        Available: ['tomopy', 'astra']
  -a ALGORITHM, --algorithm ALGORITHM
                        Reconstruction algorithm (tool dependent).
                        Available:
                        TomoPy: ['art', 'bart', 'fbp', 'gridrec', 'mlem', 'osem', 'ospml_hybrid', 'ospml_quad', 'pml_hybrid', 'pml_quad', 'sirt']
                        Astra:['FP', 'FP_CUDA', 'BP', 'BP_CUDA', 'FBP', 'FBP_CUDA', 'SIRT', 'SIRT_CUDA', 'SART', 'SART_CUDA', 'CGLS', 'CGLS_CUDA']
  -n NUM_ITER, --num-iter NUM_ITER
                        Number of iterations(only valid for iterative methods: {'art', 'bart', 'mlem', 'osem', 'ospml_hybrid', 'ospml_quad', pml_hybrid', 'pml_quad', 'sirt'}.
  --max-angle MAX_ANGLE
                        Maximum angle of the last projection.
                        Assuming first angle=0, and uniform angle increment for every projection
  --cores CORES         Number of CPU cores that will be used for reconstruction.
  --chunksize CHUNKSIZE
                        How to spread the load on each worker.
  --parallel-load       How to spread the load on each worker.

Pre-processing of input raw images/projections:
  -R [REGION_OF_INTEREST [REGION_OF_INTEREST ...]], --region-of-interest [REGION_OF_INTEREST [REGION_OF_INTEREST ...]]
                        Crop original images using these coordinates, after rotating the images.
                        If not given, the whole images are used.
                        Example: --region-of-interest='[150,234,23,22]'.
  -A [AIR_REGION [AIR_REGION ...]], --air-region [AIR_REGION [AIR_REGION ...]]
                        Air region /region for normalisation.
                        For best results it should avoid being blocked by any object.
                        Example: --air-region='[150,234,23,22]'
  --crop-before-normalise
                        Crop before doing any normalisations on the images.
                        This improves performance and reduces memory usage, asthe algorithms will work on smaller data.
  --pre-median-size PRE_MEDIAN_SIZE
                        Size / width of the median filter(pre - processing).
  --pre-median-mode {reflect,constant,nearest,mirror,wrap}
                        Default: reflect
                        Mode of median filter which determines how the array borders are handled.
  --remove-stripes REMOVE_STRIPES
                        Methods supported: 'wf' (Wavelet-Fourier).
  -r ROTATION, --rotation ROTATION
                        Rotate images by 90 degrees a number of times.
                        The rotation is clockwise unless a negative number is given which indicates rotation counterclockwise.
  --clip-min CLIP_MIN   Default: 0.0
                        Clip values after normalisations to remove out of bounds pixel values.
  --clip-max CLIP_MAX   Default: 1.5
                        Clip values after normalisations to remove out of bounds pixel values.
  --pre-outliers PRE_OUTLIERS
                        Outliers threshold for pre-processed images.
                        Pixels below this threshold with respect to maximum intensity in the stack will be set to the minimum value.
  --pre-outliers-mode {dark,bright,both}
                        Which pixels to clip, only dark ones, bright ones or both.
  --rebin REBIN         Rebin factor by which the images will be rebinned. This could be any positive float number.
                        If not specified no scaling will be done.
  --rebin-mode {nearest,lanczos,bilinear,bicubic,cubic}
                        Default: bilinear
                        Specify which interpolation mode will be used for the scaling of the image.
  -m, --mcp-corrections
                        Perform corrections specific to images taken with the MCP detector.
  --pre-gaussian-size PRE_GAUSSIAN_SIZE
                        Apply gaussian filter (2d) on reconstructed volume with the given window size.
  --pre-gaussian-mode {reflect,constant,nearest,mirror,wrap}
                        Default: reflect
                        Mode of gaussian filter which determines how the array borders are handled.(pre processing).
  --pre-gaussian-order PRE_GAUSSIAN_ORDER
                        Default: 0
                        The order of the filter along each axis is given as a sequence of integers, 
                        or as a single number. An order of 0 corresponds to convolution with a Gaussian kernel.
                        An order of 1, 2, or 3 corresponds to convolution with the first, second or third derivatives of a Gaussian.
                        Higher order derivatives are not implemented.

Post-processing of the reconstructed volume:
  --circular-mask CIRCULAR_MASK
                        Radius of the circular mask to apply on the reconstructed volume.
                        It is given in [0,1] relative to the size of the smaller dimension/edge of the slices.
                        Empty or zero implies no masking.
  --circular-mask-val CIRCULAR_MASK_VAL
                        The value that the pixels in the mask will be set to.
  --post-outliers POST_OUTLIERS
                        Outliers threshold for reconstructed volume.
                        Pixels below and/or above (depending on mode) this threshold will be clipped.
  --post-outliers-mode {dark,bright,both}
                        Which pixels to clip, only dark ones, bright ones or both.
  --post-median-size POST_MEDIAN_SIZE
                        Apply median filter (2d) on reconstructed volume with the given window size.(post processing)
  --post-median-mode {reflect,constant,nearest,mirror,wrap}
                        Default: reflect
                        Mode of median filter which determines how the array borders are handled.(post processing)
  --post-gaussian-size POST_GAUSSIAN_SIZE
                        Apply gaussian filter (2d) on reconstructed volume with the given window size.
  --post-gaussian-mode {reflect,constant,nearest,mirror,wrap}
                        Default: reflect
                        Mode of gaussian filter which determines how the array borders are handled.(post processing).
  --post-gaussian-order POST_GAUSSIAN_ORDER
                        Default: 0
                        The order of the filter along each axis is given as a sequence of integers, 
                        or as a single number. An order of 0 corresponds to convolution with a Gaussian kernel.
                        An order of 1, 2, or 3 corresponds to convolution with the first, second or third derivatives of a Gaussian.
                        Higher order derivatives are not implemented.


Reconstruction Scripts
######################


Bug Fixes
---------
- The external interpreter and scripts paths are no longer ignored and are now correctly appended when running a local reconstruction.
- Local reconstruction processes are now also updated in the reconstruction jobs list.
- The reconstruction jobs list command line is now Read Only.
- Clicking Cancel now cancels the running reconstruction process.
- The reconstruction scripts will now run with TomoPy v1.x.x, however the output is not tested with versions newer than 0.10.x.
- Selecting the Center of Rotation, Area for Normalsation and Region of Interest will now always follow the exact position of the mouse.
- Multiple success/warning/error messages will no longer be shown after an operation. 

`Full list of changes on github <http://github.com/mantidproject/mantid/pulls?q=is%3Apr+milestone%3A%22Release+3.9%22+is%3Amerged+label%3A%22Component%3A+Imaging%22>`__
